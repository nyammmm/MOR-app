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

locations = [
    ("Warehouse (San Mateo)", (14.7095, 121.1471)),
    ("SM City Taytay", (14.5733, 121.1406)),
    ("SM City Masinag", (14.6212, 121.1021)),
    ("Robinsons Place Antipolo", (14.5869, 121.1753)),
    ("Sta. Lucia East Grand Mall", (14.6096, 121.1027)),
    ("Robinsons Metro East", (14.6218, 121.1016)),
    ("SM City San Mateo", (14.6982, 121.1219)),
    ("Vista Mall Antipolo", (14.6068, 121.1761)),
    ("Shopwise Antipolo", (14.6105, 121.1743))
]

# Create distance matrix using geodesic distance (in km)
distance_matrix = []
for i in range(len(locations)):
    row = []
    for j in range(len(locations)):
        dist = geodesic(locations[i][1], locations[j][1]).km
        row.append(dist)
    distance_matrix.append(row)

# Solve TSP using OR-Tools
def solve_tsp(distance_matrix):
    manager = pywrapcp.RoutingIndexManager(len(distance_matrix), 1, 0)  # start and end at 0
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        return int(distance_matrix[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)] * 1000)

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

    solution = routing.SolveWithParameters(search_parameters)

    if not solution:
        raise Exception("No solution found!")

    # Get route
    index = routing.Start(0)
    route = []
    total_distance = 0
    while not routing.IsEnd(index):
        route.append(manager.IndexToNode(index))
        next_index = solution.Value(routing.NextVar(index))
        total_distance += routing.GetArcCostForVehicle(index, next_index, 0)
        index = next_index
    route.append(manager.IndexToNode(index))

    return route, total_distance / 1000  # Convert to km

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
