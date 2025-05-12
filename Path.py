import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import time

st.set_page_config(page_title="Optimized Route Planner", layout="wide")
st.title("🗺️ Optimal Delivery Route 🗺️")

# Sidebar for addresses
st.sidebar.header("📍 Enter Delivery Addresses")

default_addresses = [
    "Antipolo Cathedral, Antipolo, Rizal, Philippines",
    "Hinulugang Taktak, Antipolo, Rizal, Philippines",
    "Pinto Art Museum, Antipolo, Rizal, Philippines",
    "SM City Taytay, Taytay, Rizal, Philippines",
    "Angono-Binangonan Petroglyphs, Binangonan, Rizal, Philippines"
]

addresses = []
for i in range(5):
    addr = st.sidebar.text_input(f"Address {i+1}", default_addresses[i])
    if addr.strip():
        addresses.append(addr.strip())

if len(addresses) < 2:
    st.warning("Enter at least two addresses.")
    st.stop()

# Geocode using Nominatim (OpenStreetMap)
@st.cache_data
def geocode_locations(address_list):
    geolocator = Nominatim(user_agent="streamlit-route-planner")
    coords = {}
    for addr in address_list:
        location = None
        retry = 3
        while retry:
            try:
                location = geolocator.geocode(addr, timeout=10)
                break
            except Exception:
                time.sleep(1)
                retry -= 1
        if location:
            coords[addr] = (location.latitude, location.longitude)
        else:
            coords[addr] = None
    return coords

coordinates = geocode_locations(addresses)

# Validate all addresses were geocoded
for addr, coord in coordinates.items():
    if coord is None:
        st.error(f"Could not geocode: {addr}")
        st.stop()

# Compute haversine distance matrix
def compute_distance_matrix(coords):
    n = len(coords)
    matrix = [[0] * n for _ in range(n)]
    coord_list = list(coords.values())
    for i in range(n):
        for j in range(n):
            if i != j:
                matrix[i][j] = int(geodesic(coord_list[i], coord_list[j]).km * 1000)  # in meters
    return matrix

distance_matrix = compute_distance_matrix(coordinates)

# Solve TSP with OR-Tools
def solve_tsp(distance_matrix):
    manager = pywrapcp.RoutingIndexManager(len(distance_matrix), 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_idx, to_idx):
        return distance_matrix[manager.IndexToNode(from_idx)][manager.IndexToNode(to_idx)]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

    solution = routing.SolveWithParameters(search_params)
    if solution:
        index = routing.Start(0)
        route = []
        total_dist = 0
        while not routing.IsEnd(index):
            route.append(manager.IndexToNode(index))  # End node
            route.append(0)  # Explicitly return to start (node 0)
            prev_index = index
            index = solution.Value(routing.NextVar(index))
            total_dist += routing.GetArcCostForVehicle(prev_index, index, 0)
        route.append(manager.IndexToNode(index))  # return to start
        return route, total_dist / 1000  # in km
    return None, 0

route_indices, total_distance = solve_tsp(distance_matrix)

if route_indices is None:
    st.error("Could not solve route.")
    st.stop()

ordered_addresses = [addresses[i] for i in route_indices]

st.subheader("📦 Optimal Route")
for i, addr in enumerate(ordered_addresses):
    label = f"{i+1}. {addr}"
    if i == 0:
        label += " 🏁 (Start)"
    elif i == len(ordered_addresses) - 1:
        label += " 🔁 (Return)"
    st.markdown(label)

st.success(f"🚗 Total Distance: {total_distance:.2f} km")

# Map visualization
df = pd.DataFrame({
    'location': ordered_addresses,
    'lat': [coordinates[addr][0] for addr in ordered_addresses],
    'lon': [coordinates[addr][1] for addr in ordered_addresses]
})
st.map(df)
