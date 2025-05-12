import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

# App title
st.set_page_config(page_title="Rizal Delivery Optimizer", layout="wide")
st.title("📦 Optimal Delivery Route in Rizal")

# Sidebar for address input
st.sidebar.markdown("📍 **Enter Delivery Addresses**")

default_addresses = [
    "Gulod Malaya, San Mateo, Rizal, Philippines",  # Warehouse
    "SM City Taytay, Taytay, Rizal, Philippines",
    "SM City Masinag, Antipolo, Rizal, Philippines",
    "Robinsons Place Antipolo, Antipolo, Rizal, Philippines",
    "Sta. Lucia East Grand Mall, Cainta, Rizal, Philippines"
]

addresses = []
for i, default in enumerate(default_addresses):
    addr = st.sidebar.text_input(f"Address {i+1}", default)
    addresses.append(addr)

# Geocode addresses
geolocator = Nominatim(user_agent="route_optimizer")
coords = []
valid_addresses = []

for address in addresses:
    location = geolocator.geocode(address)
    if location:
        coords.append((location.latitude, location.longitude))
        valid_addresses.append(location.address)
    else:
        st.error(f"Could not geocode: {address}")
        st.stop()

# Distance matrix using geodesic distance
def compute_distance_matrix(coords):
    n = len(coords)
    matrix = []
    for i in range(n):
        row = []
        for j in range(n):
            if i == j:
                row.append(0)
            else:
                dist = geodesic(coords[i], coords[j]).km
                row.append(dist)
        matrix.append(row)
    return matrix

# TSP Solver using OR-Tools
def solve_tsp(distance_matrix):
    n = len(distance_matrix)
    manager = pywrapcp.RoutingIndexManager(n, 1, 0)  # start and end at node 0
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_idx, to_idx):
        from_node = manager.IndexToNode(from_idx)
        to_node = manager.IndexToNode(to_idx)
        return int(distance_matrix[from_node][to_node] * 1000)  # convert to meters

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Make it return to the starting point
    routing.SetRoutingStrategy(routing_enums_pb2.RoutingStrategy.GLOBAL_CHEAPEST_ARC)
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

    solution = routing.SolveWithParameters(search_parameters)

    if solution:
        index = routing.Start(0)
        route = []
        total_distance = 0
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            route.append(node_index)
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            total_distance += routing.GetArcCostForVehicle(previous_index, index, 0)
        route.append(manager.IndexToNode(index))
        return route, total_distance / 1000  # convert back to km
    else:
        st.error("No solution found for route optimization.")
        st.stop()

# Compute route
distance_matrix = compute_distance_matrix(coords)
route, total_distance = solve_tsp(distance_matrix)
ordered_addresses = [valid_addresses[i] for i in route]

# Display route
st.markdown("## 📦 Optimal Route")
for i, addr in enumerate(ordered_addresses):
    if i == 0:
        st.markdown(f"**{i+1}. {addr} 🏁 (Start)**")
    elif i == len(ordered_addresses) - 1:
        st.markdown(f"**{i+1}. {addr} 🔁 (Return)**")
    else:
        st.markdown(f"{i+1}. {addr}")

# Display total distance
st.success(f"🚗 Total Distance: {total_distance:.2f} km")

# Map visualization
m = folium.Map(location=coords[0], zoom_start=11)
for i, idx in enumerate(route):
    folium.Marker(
        location=coords[idx],
        popup=f"{i+1}: {valid_addresses[idx]}",
        icon=folium.Icon(color="blue" if i != 0 else "green")
    ).add_to(m)

# Draw route
route_coords = [coords[i] for i in route]
folium.PolyLine(locations=route_coords, color="blue", weight=3).add_to(m)

# Show map
st_data = st_folium(m, width=800, height=500)
