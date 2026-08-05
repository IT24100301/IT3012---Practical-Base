import random
import tkinter as tk

class VisualGridHuntGame:
    """A flexible Pacman-style grid environment updated for Partial Observability."""
    def __init__(self, width=10, height=10, num_food=10, num_opponents=2, num_traps=4, custom_walls=None):
        self.width = width
        self.height = height
        self.agent_pos = [0, 0] 
        
        
        self.last_action = 'Right' 
        

        if custom_walls is not None:
            self.walls = set(custom_walls)
        else:
            # Layout containing a clear corner/trap to trigger reflex failure
            self.walls = {(1, 2), (2, 2), (2, 1), (5, 5), (6, 5)} 

        self.food_positions = set()
        while len(self.food_positions) < num_food:
            fx = random.randint(0, self.width - 1)
            fy = random.randint(0, self.height - 1)
            if (fx, fy) != (0, 0) and (fx, fy) not in self.walls:
                self.food_positions.add((fx, fy))

        self.toxic_traps = set()
        while len(self.toxic_traps) < num_traps:
            tx = random.randint(0, self.width - 1)
            ty = random.randint(0, self.height - 1)
            if (tx, ty) != (0, 0) and (tx, ty) not in self.walls and (tx, ty) not in self.food_positions:
                self.toxic_traps.add((tx, ty))

        self.opponents = []
        while len(self.opponents) < num_opponents:
            ox = random.randint(0, self.width - 1)
            oy = random.randint(0, self.height - 1)
            if (ox, oy) != (0, 0) and (ox, oy) not in self.walls and (ox, oy) not in self.food_positions:
                self.opponents.append([ox, oy])

        self.score = 0
        self.steps = 0
        self.collision = False

    # --- STEP 1.1: EXACT COMPLIANCE FOR PARTIAL OBSERVABILITY ---
    def get_percept(self) -> dict:
        """Returns ONLY local booleans based strictly on adjacent cells."""
        x, y = self.agent_pos
        next_x, next_y = x, y

        # Check adjacent cell in its current facing direction (last_action)
        if self.last_action == 'Up':
            next_y = y + 1
        elif self.last_action == 'Down':
            next_y = y - 1
        elif self.last_action == 'Left':
            next_x = x - 1
        elif self.last_action == 'Right':
            next_x = x + 1

        # Determine if there is an obstruction ahead
        out_of_bounds = (next_x < 0 or next_x >= self.width or next_y < 0 or next_y >= self.height)
        wall_ahead = out_of_bounds or ((next_x, next_y) in self.walls)
        
        # Check current tile condition
        food_here = tuple(self.agent_pos) in self.food_positions

        # Returns ONLY the requested local booleans
        return {
            'wall_ahead': wall_ahead,
            'food_here': food_here
        }

    def execute_action(self, action: str):
        """Processes standard grid actions: Up, Down, Left, Right, Suck."""
        self.steps += 1
        
        if action == 'Suck':
            tuple_pos = tuple(self.agent_pos)
            if tuple_pos in self.food_positions:
                self.food_positions.remove(tuple_pos)
                self.score += 20
            return

        # Keep track of active facing direction vector
        if action in ['Up', 'Down', 'Left', 'Right']:
            self.last_action = action

        new_pos = list(self.agent_pos)
        if action == 'Up':
            new_pos[1] = min(self.height - 1, new_pos[1] + 1)
        elif action == 'Down':
            new_pos[1] = max(0, new_pos[1] - 1)
        elif action == 'Left':
            new_pos[0] = max(0, new_pos[0] - 1)
        elif action == 'Right':
            new_pos[0] = min(self.width - 1, new_pos[0] + 1)

        if tuple(new_pos) in self.walls:
            self.score -= 5 # Wall collision penalty
        else:
            self.agent_pos = new_pos

        tuple_pos = tuple(self.agent_pos)
        if tuple_pos in self.toxic_traps:
            self.score -= 15

        for op in self.opponents:
            move = random.choice(['Up', 'Down', 'Left', 'Right', 'Stay'])
            if move == 'Up' and op[1] < self.height - 1: op[1] += 1
            elif move == 'Down' and op[1] > 0: op[1] -= 1
            elif move == 'Left' and op[0] > 0: op[0] -= 1
            elif move == 'Right' and op[0] < self.width - 1: op[0] += 1
            if op == self.agent_pos:
                self.score -= 50
                self.collision = True

    def is_done(self) -> bool:
        return len(self.food_positions) == 0 or self.steps >= 60 or self.collision


# --- STEP 1.2: COMPLIANT SIMPLE REFLEX AGENT ---
class SimpleReflexAgent:
    """Uses strictly stateless IF-THEN rules matching the example scenario."""
    def sense_and_act(self, percept: dict) -> str:
        if percept['food_here']:
            return 'Suck'
        if percept['wall_ahead']:
            return 'Up'  # Forces a directional adjustment switch when stuck
        else:
            return 'Right' # Default directional baseline movement


# --- STEP 1.3: COMPLIANT MODEL-BASED AGENT ---
class ModelBasedAgent:
    """Maintains an internal relative map state to track local movement patterns."""
    def __init__(self):
        # State tracking fields
        self.current_rel_pos = (0, 0)
        self.visited_relative_positions = { (0, 0) }
        self.last_agent_action = 'Right'

    def sense_and_act(self, percept: dict) -> str:
        # 1. Update State (Transition & Sensor Model) based on last action and current percept
        rx, ry = self.current_rel_pos
        
        # Only adjust our tracking coordinates if the last action didn't hit a wall ahead
        if not percept['wall_ahead']:
            if self.last_agent_action == 'Up': ry += 1
            elif self.last_agent_action == 'Down': ry -= 1
            elif self.last_agent_action == 'Left': rx -= 1
            elif self.last_agent_action == 'Right': rx += 1
            
        self.current_rel_pos = (rx, ry)
        self.visited_relative_positions.add(self.current_rel_pos)

        # Evaluate adjacent positions relative to current spot to verify loop behaviors
        left_pos = (rx - 1, ry)
        left_is_visited = left_pos in self.visited_relative_positions

        # 2. Rule Selection matching your exact criteria examples
        if percept['food_here']:
            action = 'Suck'
        elif percept['wall_ahead'] and left_is_visited:
            action = 'Up'
        elif percept['wall_ahead']:
            action = 'Left'
        else:
            action = 'Right'

        # Record action before returning to use in the next step's transition update
        self.last_agent_action = action
        return action


class GridGameGUI:
    def __init__(self, root, width=10, height=10, num_food=12, num_opponents=0, num_traps=4, walls=None):
        self.root = root
        self.root.title("IT3012 - Scalable Multi-Agent Grid Hunt")
        self.env = VisualGridHuntGame(width=width, height=height, num_food=num_food, num_opponents=num_opponents, num_traps=num_traps, custom_walls=walls)
        
        # ----------------------------------------------------
        # HOW TO RUN SIMULATION FOR STEP 1.2 & 1.3:
        # Toggle between these lines to test different architectures
        #self.agent = SimpleReflexAgent() #step 1.2
        self.agent = ModelBasedAgent()    #step 1.3

        max_canvas_dim = 600
        self.cell_size = max(20, min(max_canvas_dim // self.env.width, max_canvas_dim // self.env.height))
        self.canvas = tk.Canvas(root, width=self.env.width * self.cell_size, height=self.env.height * self.cell_size, bg="white")
        self.canvas.pack()
        self.label = tk.Label(root, text="Score: 0 | Steps: 0", font=("Arial", 14))
        self.label.pack(pady=10)
        self.btn = tk.Button(root, text="Start Simulation", command=self.run_loop, font=("Arial", 12), bg="#000066", fg="white")
        self.btn.pack(pady=5)
        self.draw_grid()

    def draw_grid(self):
        self.canvas.delete("all")
        for x in range(self.env.width):
            for y in range(self.env.height):
                x1, y1 = x * self.cell_size, (self.env.height - 1 - y) * self.cell_size
                x2, y2 = x1 + self.cell_size, y1 + self.cell_size
                color = "#f1f5f9" if (x, y) not in self.env.walls else "#64748b"
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#cbd5e1")

        for fx, fy in self.env.food_positions:
            offset = self.cell_size * 0.25
            self.canvas.create_oval(fx*self.cell_size+offset, (self.env.height-1-fy)*self.cell_size+offset, fx*self.cell_size+offset+self.cell_size*0.5, (self.env.height-1-fy)*self.cell_size+offset+self.cell_size*0.5, fill="#f59e0b")

        ax, ay = self.env.agent_pos
        offset = self.cell_size * 0.15
        self.canvas.create_oval(ax*self.cell_size+offset, (self.env.height-1-ay)*self.cell_size+offset, ax*self.cell_size+offset+self.cell_size*0.7, (self.env.height-1-ay)*self.cell_size+offset+self.cell_size*0.7, fill="#000066")

    def run_loop(self):
        self.btn.config(state="disabled")
        def step():
            if not self.env.is_done():
                percept = self.env.get_percept()
                action = self.agent.sense_and_act(percept)
                self.env.execute_action(action)
                self.draw_grid()
                self.label.config(text=f"Score: {self.env.score} | Steps: {self.env.steps} | Action: {action}")
                self.root.after(200, step)
            else:
                self.label.config(text=f"Finished! Final Score: {self.env.score}")
                self.btn.config(state="normal")
        step()

if __name__ == "__main__":
    root = tk.Tk()
    app = GridGameGUI(root)
    root.mainloop()