import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from math import radians, sin, cos, sqrt, atan2

st.set_page_config(layout="wide")
st.title("📦 Optimal Delivery Route in Rizal")

st.sidebar.header("📍 Enter Delivery Addresses and Coordinates")

# Sample default data
sample_addresses = [
    "Gulod Malaya, San Mateo, Rizal, Philippines",
    "SM City Taytay, Taytay, Rizal, Philippines",
    "SM City Masinag, Antipolo, Rizal, Philippines",
    "Robinsons Place Antipolo, Antipolo, Rizal, Philippines",
    "Sta. Lucia East Grand Mall, Cainta, Rizal, Philippines"
]

sample_coords = [
    (14.7104, 121.1213),  # Gulod Malaya
    (14.5764, 121.1323),  # SM Taytay
    (14.6211, 121.1233),  # SM Masinag
    (14.5869, 121.1755),  # Robinsons Antipolo
    (14.6082, 121.1110),  # Sta Lucia East
]

if st.sidebar.button("🔁 Reset to Sample Data"):
    st.session_state.reset_requested = True

if "reset_requested" not in st.session_state:
    st.session_state.reset_requested = False

if st.session_state.reset_requested:
    st.session_state.reset_requested = False
    st.session_state.address_inputs = sample_addresses.copy()
    st.session_state.lat_inputs = [str(coord[0]) for coord in sample_coords]
    st.session_state.lon_inputs = [str(coord[1]) for coord in sample_coords]

num_locations = st.sidebar.number_input("Number of Locations", min_value=2, max_value=15, value=len(sample_addresses), step=1)

addresses = []
coords = []
for i in range(num_locations):
    default_address = sample_addresses[i] if i < len(sample_addresses) else ""
    default_lat = str(sample_coords[i][0]) if i < len(sample_coords) else ""
    default_lon = str(sample_coords[i][1]) if i < len(sample_coords) else ""

    default_address_input = st.session_state.get("address_inputs", [default_address] * num_locations)[i] if len(st.session_state.get("address_inputs", [])) > i else default_address
    default_lat_input = st.session_state.get("lat_inputs", [default_lat] * num_locations)[i] if len(st.session_state.get("lat_inputs", [])) > i else default_lat
    default_lon_input = st.session_state.get("lon_inputs", [default_lon] * num_locations)[i] if len(st.session_state.get("lon_inputs", [])) > i else default_lon

    address = st.sidebar.text_input(f"Address {i+1}", value=default_address_input, key=f"address_{i}")
    lat = st.sidebar.text_input(f"Latitude {i+1}", value=default_lat_input, key=f"lat_{i}")
    lon = st.sidebar.text_input(f"Longitude {i+1}", value=default_lon_input, key=f"lon_{i}")

    if address and lat and lon:
        try:
            lat = float(lat)
            lon = float(lon)
            addresses.append(address)
            coords.append((lat, lon))
        except ValueError:
            st.sidebar.error(f"Invalid coordinates for Address {i+1}")

# Haversine distance calculator
def haversine(coord1, coord2):
    R = 6371.0
    lat1, lon1 = radians(coord1[0]), radians(coord1[1])
    lat2, lon2 = radians(coord2[0]), radians(coord2[1]
    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance

def create_distance_matrix(locations):
    size = len(locations)
    matrix = []
    for i in range(size):
        row = []
        for j in range(size):
            row.append(haversine(locations[i], locations[j]))
        matrix.append(row)
    return matrix

def solve_tsp(distance_matrix):
    manager = pywrapcp.RoutingIndexManager(len(distance_matrix), 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(distance_matrix[from_node][to_node] * 1000)

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

    solution = routing.SolveWithParameters(search_parameters)

    if solution:
        index = routing.Start(0)
        route = []
        route_distance = 0
        while not routing.IsEnd(index):
            route.append(manager.IndexToNode(index))
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(previous_index, index, 0)
        route.append(manager.IndexToNode(index))  # return to start
        return route, route_distance / 1000  # convert to km
    else:
        return None, None

if len(coords) >= 2:
    distance_matrix = create_distance_matrix(coords)
    route_indices, total_distance = solve_tsp(distance_matrix)

    if route_indices:
        st.subheader("📦 Optimal Route")
        for idx, i in enumerate(route_indices):
            if idx == 0:
                st.markdown(f"**{idx+1}.** {addresses[i]} 🏁 (Start)")
            elif idx == len(route_indices) - 1:
                st.markdown(f"**{idx+1}.** {addresses[i]} 🔁 (Return)")
            else:
                st.markdown(f"**{idx+1}.** {addresses[i]}")

        st.success(f"🚗 Total Distance: {total_distance:.2f} km")

        m = folium.Map(location=coords[0], zoom_start=11)
        for idx, i in enumerate(route_indices):
            folium.Marker(coords[i], tooltip=f"{idx+1}: {addresses[i]}").add_to(m)
        st_folium(m, width=700, height=500)
    else:
        st.error("Unable to compute optimal route.")
else:
    st.info("Please input at least 2 valid addresses with coordinates.")
