import pandas as pd
from collections import defaultdict, deque

# -------------------
# 1. Read Inputs from CSV Files
# -------------------
systems_df = pd.read_csv("systems.csv")
pipes_df = pd.read_csv("pipes.csv")
flows_df = pd.read_csv("initial_flows.csv")

systems = {row['system']: {'supply': row['supply'], 'demand': row['demand']} for _, row in systems_df.iterrows()}

pipe_capacities = {(row['from'], row['to']): row['capacity'] for _, row in pipes_df.iterrows()}

pre_existing_flows = {(row['from'], row['to']): row['flow'] for _, row in flows_df.iterrows()}

# -------------------
# 2. Initial Balance Check
# -------------------
for system, values in systems.items():
    local_supply = values['supply']
    incoming_flows = sum(flow for (src, dst), flow in pre_existing_flows.items() if dst == system)
    total_available = local_supply + incoming_flows

    if total_available < values['demand']:
        raise ValueError(f"❌ System {system} starts with a shortage!")

# -------------------
# 3. Netting Flows
# -------------------
net_flows = defaultdict(float)

for (from_system, to_system), flow in pre_existing_flows.items():
    net_flows[(from_system, to_system)] += flow
    net_flows[(to_system, from_system)] -= flow

# Cancel counterflows (keep dominant direction)
final_flows = defaultdict(float)
for (a, b), net_flow in net_flows.items():
    if net_flow > 0:
        final_flows[(a, b)] = net_flow

# -------------------
# 4. Balance Check After Netting
# -------------------
def compute_system_balance(final_flows):
    balance = defaultdict(float)
    for system, values in systems.items():
        balance[system] = values['supply'] - values['demand']

    for (a, b), flow in final_flows.items():
        balance[a] -= flow
        balance[b] += flow

    return balance


balances = compute_system_balance(final_flows)

print("\nSystem Balance After Netting:")
for system, bal in balances.items():
    print(f"  {system}: {bal:.2f} MW")

# -------------------
# 5. Rescue Flows Using Paths (Capacity-Aware & Safe)
# -------------------
graph = defaultdict(list)
for (a, b), cap in pipe_capacities.items():
    graph[a].append((b, cap))
    graph[b].append((a, cap))


def find_path(source, target, needed):
    queue = deque([(source, [], float('inf'))])
    visited = set()

    while queue:
        current, path, capacity = queue.popleft()

        if current == target:
            return path, capacity

        if current in visited:
            continue
        visited.add(current)

        for neighbor, cap in graph[current]:
            if neighbor not in visited:
                available = min(cap, capacity)
                queue.append((neighbor, path + [(current, neighbor)], available))

    return None, 0


while any(bal < 0 for bal in balances.values()):
    progress_made = False

    for system, bal in balances.items():
        if bal < 0:
            for donor, donor_balance in balances.items():
                if donor_balance > 0:
                    path, capacity = find_path(donor, system, -bal)

                    if path:
                        flow_amount = min(-bal, donor_balance, capacity)

                        for (a, b) in path:
                            final_flows[(a, b)] += flow_amount

                        balances = compute_system_balance(final_flows)

                        print(f"Rescue Flow: {donor} → {system} via {path}: {flow_amount:.2f} MW")
                        progress_made = True
                        break

            if progress_made:
                break

    if not progress_made:
        print(f"⚠️ Could not resolve shortage for one or more systems. Capacity or connections are insufficient.")
        break

# -------------------
# 6. Final Output
# -------------------
print("\n=== FINAL SOLUTION ===")

print("System Balances:")
for system, bal in balances.items():
    status = "✅ Balanced" if bal == 0 else "❌ Shortage"
    print(f"  {system}: {bal:.2f} MW ({status})")

print("\nFinal Flows:")
for (a, b), flow in final_flows.items():
    if flow > 0:
        print(f"  {a} → {b}: {flow:.2f} MW")

print("\nPipe Utilization:")
for (a, b), capacity in pipe_capacities.items():
    used_flow = final_flows.get((a, b), 0)
    print(f"  {a} → {b}: {used_flow:.2f} MW / {capacity} MW")
