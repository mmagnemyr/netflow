from collections import defaultdict


# --------------------------
# 1. CONFIG: Systems and Flows
# --------------------------
systems = {
    'A': {'supply': 5, 'demand': 3},
    'B': {'supply': 2, 'demand': 4},
    'C': {'supply': 0, 'demand': 2},
    'D': {'supply': 4, 'demand': 3}
}

flows = [
    ('A', 'B', 3),
    ('B', 'A', 1),
    ('B', 'C', 2),
    ('C', 'B', 0),
    ('A', 'D', 1),
    ('D', 'A', 0)
]

# --------------------------
# 2. Display Initial Setup
# --------------------------
print("\n--- INITIAL SITUATION ---")
print("Systems (Supply & Demand):")
for system, values in systems.items():
    print(f"{system}: Supply={values['supply']}MW, Demand={values['demand']}MW")

print("\nFlows (Initial bidirectional flows):")
for f in flows:
    print(f"{f[0]} → {f[1]}: {f[2]} MW")

# --------------------------
# 3. Calculate Net Flows (Combining bidirectional flows)
# --------------------------
net_flows = defaultdict(float)

for from_node, to_node, flow in flows:
    key = tuple(sorted([from_node, to_node]))
    if key == (from_node, to_node):
        net_flows[key] += flow
    else:
        net_flows[key] -= flow

# --------------------------
# 4. Calculate System Balances
# --------------------------
net_energy_balance = defaultdict(float)

# Apply net flows
for (a, b), net_flow in net_flows.items():
    if net_flow > 0:
        net_energy_balance[a] -= net_flow
        net_energy_balance[b] += net_flow
    elif net_flow < 0:
        net_energy_balance[a] += abs(net_flow)
        net_energy_balance[b] -= abs(net_flow)

# Add local supply and demand
for system, values in systems.items():
    net_energy_balance[system] += values['supply'] - values['demand']

# --------------------------
# 5. Display Net Flows + Balances Before Adjustment
# --------------------------
print("\n--- NET FLOWS (Dominant Directions) ---")
for (a, b), net_flow in net_flows.items():
    if net_flow > 0:
        print(f"{a} → {b}: {net_flow:.2f} MW")
    elif net_flow < 0:
        print(f"{b} → {a}: {abs(net_flow):.2f} MW")
    else:
        print(f"{a} ↔ {b}: No net flow")

print("\n--- ENERGY BALANCE (Before Adjustment) ---")
shortages = {}
surpluses = {}

for system, balance in net_energy_balance.items():
    status = "✅ OK" if balance >= 0 else "❌ SHORTAGE"
    if balance < 0:
        shortages[system] = -balance
    elif balance > 0:
        surpluses[system] = balance
    print(f"{system}: {balance:.2f} MW ({status})")

# --------------------------
# 6. Attempt to Fix Shortages Greedily
# --------------------------
new_flows = []

for shortage_system, shortage_amount in shortages.items():
    for surplus_system, surplus_amount in surpluses.items():
        if surplus_amount <= 0:
            continue

        # Determine how much we can transfer
        transfer_amount = min(shortage_amount, surplus_amount)

        # Create a flow to cover the shortage
        new_flows.append((surplus_system, shortage_system, transfer_amount))

        # Update the balances and surpluses
        net_energy_balance[shortage_system] += transfer_amount
        net_energy_balance[surplus_system] -= transfer_amount

        shortages[shortage_system] -= transfer_amount
        surpluses[surplus_system] -= transfer_amount

        # If this shortage is resolved, stop searching
        if shortages[shortage_system] <= 0:
            break

# --------------------------
# 7. Display New Flows
# --------------------------
if new_flows:
    print("\n--- ADDED FLOWS TO BALANCE SHORTAGES ---")
    for from_node, to_node, flow in new_flows:
        print(f"{from_node} → {to_node}: {flow:.2f} MW")
else:
    print("\n✅ No additional flows needed.")

# --------------------------
# 8. Final Check and Display
# --------------------------
print("\n--- FINAL ENERGY BALANCE ---")
for system, balance in net_energy_balance.items():
    status = "✅ OK" if balance >= 0 else "❌ SHORTAGE"
    print(f"{system}: {balance:.2f} MW ({status})")

# --------------------------
# 9. Optional: Combine Original and New Flows
# --------------------------
combined_flows = flows + new_flows

print("\n--- FINAL FLOW PLAN ---")
for f in combined_flows:
    print(f"{f[0]} → {f[1]}: {f[2]:.2f} MW")
