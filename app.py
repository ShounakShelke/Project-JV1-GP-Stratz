import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from env.race_env import RaceEnvironment
from agents import AGENT_REGISTRY, AGENT_META
from graders.phase_grader import run_phase, PHASE_SCENARIOS

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TASKS = [
    {"id": "easy", "task_id": "easy", "grader": "deterministic"},
    {"id": "medium", "task_id": "medium", "grader": "deterministic"},
    {"id": "hard", "task_id": "hard", "grader": "deterministic"},
]

global_env = RaceEnvironment(max_laps=30)

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GP-Stratz</title>
    <style>
        :root {
            --bg: #0B0F19;
            --panel: #111827;
            --panel-border: #1F2937;
            --text: #F3F4F6;
            --text-muted: #9CA3AF;
            --accent-start: #6366f1;
            --accent-end: #a855f7;
            --success: #10B981;
            --danger: #EF4444;
            --font: 'Inter', system-ui, -apple-system, sans-serif;
        }

        body {
            margin: 0;
            padding: 0;
            background-color: var(--bg);
            color: var(--text);
            font-family: var(--font);
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        nav {
            width: 100%;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 40px;
            box-sizing: border-box;
            border-bottom: 1px solid var(--panel-border);
            background: rgba(11, 15, 25, 0.8);
            backdrop-filter: blur(10px);
        }

        .nav-logo {
            font-size: 1.25rem;
            font-weight: bold;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .nav-links {
            display: flex;
            gap: 20px;
            align-items: center;
        }

        .nav-links a {
            color: var(--text-muted);
            text-decoration: none;
            font-size: 0.9rem;
            transition: color 0.2s;
        }
        .nav-links a:hover { color: var(--text); }
        .nav-links .pill {
            background: linear-gradient(to right, var(--accent-start), var(--accent-end));
            color: white;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
        }

        .hero {
            text-align: center;
            margin: 60px 0 40px 0;
            max-width: 800px;
        }

        .hero h1 {
            font-size: 3.5rem;
            margin: 0 0 20px 0;
            background: linear-gradient(to right, #e2e8f0, #94a3b8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            line-height: 1.2;
        }

        .hero p {
            color: var(--text-muted);
            font-size: 1.1rem;
            line-height: 1.6;
            margin: 0 0 10px 0;
        }
        
        .hero .highlight {
            color: var(--success);
        }

        .dashboard {
            display: grid;
            grid-template-columns: 300px 1fr 400px;
            gap: 20px;
            width: 100%;
            max-width: 1400px;
            padding: 0 20px;
            box-sizing: border-box;
        }

        .panel {
            background: var(--panel);
            border: 1px solid var(--panel-border);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
        }

        .panel h2 {
            margin: 0 0 15px 0;
            font-size: 1.1rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        select {
            width: 100%;
            background: #1F2937;
            color: white;
            border: 1px solid #374151;
            padding: 12px;
            border-radius: 8px;
            font-size: 0.95rem;
            margin-bottom: 15px;
            outline: none;
        }

        .run-btn {
            width: 100%;
            background: linear-gradient(to right, var(--accent-start), var(--accent-end));
            color: white;
            border: none;
            padding: 12px;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: bold;
            cursor: pointer;
            transition: opacity 0.2s, transform 0.1s;
        }

        .run-btn:hover { opacity: 0.9; }
        .run-btn:active { transform: scale(0.98); }
        .run-btn:disabled { opacity: 0.5; cursor: not-allowed; }

        .terminal {
            background: #000;
            border-radius: 8px;
            height: 300px;
            overflow-y: auto;
            font-family: 'Menlo', 'Monaco', monospace;
            font-size: 0.85rem;
            padding: 15px;
            color: #A0AEC0;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.5);
            border: 1px solid #1a202c;
        }
        
        .mac-dots {
            display: flex;
            gap: 6px;
            margin-bottom: 15px;
        }
        .dot { width: 12px; height: 12px; border-radius: 50%; }
        .dot.red { background: #FF5F56; }
        .dot.yellow { background: #FFBD2E; }
        .dot.green { background: #27C93F; }

        .log-entry { margin-bottom: 5px; }
        .log-entry.pit { color: #f59e0b; }
        .log-entry.push { color: #ef4444; }
        .log-entry.conserve { color: #10b981; }

        /* Bottom Sections */
        .bottom-sections {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
            width: 100%;
            max-width: 1400px;
            padding: 20px;
            box-sizing: border-box;
            margin-bottom: 50px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th, td {
            text-align: center;
            padding: 12px;
            border-bottom: 1px solid var(--panel-border);
        }

        th {
            color: var(--text-muted);
            font-size: 0.85rem;
            font-weight: 500;
        }

        .telemetry-box {
            background: rgba(0,0,0,0.2);
            border: 1px solid var(--panel-border);
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 15px;
            text-align: center;
        }

        .lap-counter {
            font-size: 4rem;
            font-weight: 900;
            background: linear-gradient(to right, #fff, #9ca3af);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }

        .tyre-bar-wrapper {
            width: 100%;
            background: #1F2937;
            height: 12px;
            border-radius: 6px;
            overflow: hidden;
            margin-top: 10px;
        }

        .tyre-bar-fill {
            height: 100%;
            width: 0%;
            background: var(--success);
            transition: width 0.3s ease, background 0.3s ease;
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            background: #1F2937;
            padding: 10px 15px;
            border-radius: 6px;
            font-size: 0.9rem;
        }
        .metric-label { color: var(--text-muted); }
        .metric-value { font-weight: bold; }

        /* Timeline bar */
        .timeline-container {
            display: flex;
            align-items: flex-end;
            height: 150px;
            gap: 4px;
            border-bottom: 1px solid var(--panel-border);
            padding-bottom: 10px;
        }
        .time-bar {
            flex: 1;
            background: var(--accent-start);
            border-radius: 2px 2px 0 0;
            transition: height 0.3s;
            position: relative;
        }
        .time-bar:hover::after {
            content: attr(data-val);
            position: absolute;
            top: -25px;
            left: 50%;
            transform: translateX(-50%);
            background: #fff;
            color: #000;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.75rem;
            pointer-events: none;
            z-index: 10;
        }
    </style>
</head>
<body>
    <nav>
        <div class="nav-logo">
            <span style="color: var(--accent-start)">●</span> GP-Stratz
        </div>
        <div class="nav-links">
            <a href="#">GitHub</a>
            <a href="#">Paper</a>
            <span class="pill">Meta PyTorch × Scaler 2026</span>
        </div>
    </nav>

    <div class="hero">
        <h1>The AI That Masters F1 Strategy</h1>
        <p>GP-Stratz trains LLM agents to declare <strong style="color:white;">calibrated confidence</strong> through adversarial tyre management. Overconfident? <span class="highlight" style="color:var(--danger)">Penalised.</span> Tactical management? <span class="highlight">Rewarded.</span></p>
        <p>The <strong>Multi-Agent Optimizer</strong> below simulates the full GP environment. Watch it unfold.</p>
    </div>

    <div class="dashboard">
        <div class="panel">
            <h2>Run an Episode</h2>
            <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 20px;">Pick a phase, pick an agent, click Run, and watch the agent navigate weather and tyre degradation.</p>
            
            <select id="phase-select">
                <option value="easy">Easy (Weather & Wear)</option>
                <option value="medium">Medium (+ SC & Traffic)</option>
                <option value="hard">Hard (Optimizer)</option>
            </select>

            <select id="agent-select">
                <option value="easy">EasyRuleAgent</option>
                <option value="medium">MediumAgent</option>
                <option value="hard">HardMultiFactorAgent</option>
                <option value="conservative">ConservativeAgent</option>
                <option value="aggressive">AggressiveAgent</option>
            </select>

            <button id="run-btn" class="run-btn" onclick="runEpisode()">▶ Run Episode</button>
            <button onclick="runMatrix()" class="run-btn" style="margin-top:10px; background: #374151; color: white;">Run Full Matrix</button>
        </div>

        <div class="panel">
            <h2>Live Telemetry</h2>
            <div class="telemetry-box">
                <div class="lap-counter">LAP <span id="lap-display">0</span>/30</div>
                <div style="display: flex; justify-content: space-between; font-size: 0.85rem; color: var(--text-muted);">
                    <span>Tyre Wear</span>
                    <span id="wear-val">0%</span>
                </div>
                <div class="tyre-bar-wrapper">
                    <div class="tyre-bar-fill" id="tyre-bar"></div>
                </div>
            </div>
            
            <div class="metrics-grid">
                <div class="metric"><span class="metric-label">Reward</span><span class="metric-value" id="score-val">0.00</span></div>
                <div class="metric"><span class="metric-label">Status</span><span class="metric-value" id="status-val">-</span></div>
                <div class="metric"><span class="metric-label">Weather</span><span class="metric-value" id="weather-val">CLEAR</span></div>
                <div class="metric"><span class="metric-label">Gap</span><span class="metric-value" id="gap-val">5.0s</span></div>
            </div>
        </div>

        <div class="panel" style="padding: 0; background: transparent; border: none; box-shadow: none;">
            <div class="terminal">
                <div class="mac-dots">
                    <div class="dot red"></div>
                    <div class="dot yellow"></div>
                    <div class="dot green"></div>
                    <span style="margin-left: 10px; font-family: var(--font); font-size: 0.8rem; color: #6B7280;">agent-trace.log</span>
                </div>
                <div id="log-box">Waiting for episode to start...</div>
            </div>
        </div>
    </div>

    <div class="bottom-sections">
        <div class="panel">
            <h2>Reward Timeline</h2>
            <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 20px;">Displays the step-by-step reward allocation across the 30-lap episode.</p>
            <div class="timeline-container" id="timeline"></div>
        </div>

        <div class="panel">
            <h2>Leaderboard Matrix</h2>
            <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 20px;">Rows = Agent, Cols = Phase</p>
            <table>
                <thead>
                    <tr>
                        <th style="text-align: left;">Agent</th>
                        <th>Easy</th>
                        <th>Med</th>
                        <th>Hard</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="text-align: left; color: #fff;">EasyRule</td>
                        <td id="lb-easy-easy">-</td>
                        <td id="lb-easy-medium">-</td>
                        <td id="lb-easy-hard">-</td>
                    </tr>
                    <tr>
                        <td style="text-align: left; color: #fff;">Medium</td>
                        <td id="lb-medium-easy">-</td>
                        <td id="lb-medium-medium">-</td>
                        <td id="lb-medium-hard">-</td>
                    </tr>
                    <tr>
                        <td style="text-align: left; color: #fff;">HardOpt</td>
                        <td id="lb-hard-easy">-</td>
                        <td id="lb-hard-medium">-</td>
                        <td id="lb-hard-hard">-</td>
                    </tr>
                    <tr>
                        <td style="text-align: left; color: #fff;">Conserv</td>
                        <td id="lb-conservative-easy">-</td>
                        <td id="lb-conservative-medium">-</td>
                        <td id="lb-conservative-hard">-</td>
                    </tr>
                    <tr>
                        <td style="text-align: left; color: #fff;">Aggress</td>
                        <td id="lb-aggressive-easy">-</td>
                        <td id="lb-aggressive-medium">-</td>
                        <td id="lb-aggressive-hard">-</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <script>
        const API_BASE = window.location.origin;
        const actions = {0: "PIT", 1: "STAY", 2: "CONSERVE", 3: "PUSH", 4: "SWAP"};

        function log(msg, cls="") {
            const b = document.getElementById("log-box");
            if(b.textContent === "Waiting for episode to start...") b.innerHTML = "";
            const d = document.createElement("div");
            d.className = "log-entry " + cls;
            d.textContent = msg;
            b.appendChild(d);
            b.scrollTop = b.scrollHeight;
        }

        async function runEpisode() {
            const phase = document.getElementById("phase-select").value;
            const agent = document.getElementById("agent-select").value;
            const btn = document.getElementById("run-btn");
            
            btn.disabled = true;
            btn.textContent = "Running...";
            document.getElementById("log-box").innerHTML = "";
            document.getElementById("timeline").innerHTML = "";
            document.getElementById("status-val").textContent = "RUNNING";
            document.getElementById("status-val").style.color = "var(--text)";

            log(`> Starting ${agent} on ${phase}...`);

            try {
                const res = await fetch(`${API_BASE}/agents/${agent}/run`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({task_id: phase})
                });
                const data = await res.json();
                animate(data.breakdown_per_lap, data.score);
            } catch(e) {
                log(`> Error: ${e.message}`, "push");
                btn.disabled = false;
                btn.textContent = "▶ Run Episode";
            }
        }

        function animate(breakdown, finalScore) {
            let i = 0;
            let wear = 0;
            let gap = 5.0;
            const timeline = document.getElementById("timeline");
            
            const intv = setInterval(() => {
                if(i >= breakdown.length) {
                    clearInterval(intv);
                    document.getElementById("score-val").textContent = finalScore.toFixed(3);
                    const pass = finalScore > 0.0;
                    document.getElementById("status-val").textContent = pass ? "PASS" : "FAIL";
                    document.getElementById("status-val").style.color = pass ? "var(--success)" : "var(--danger)";
                    document.getElementById("run-btn").disabled = false;
                    document.getElementById("run-btn").textContent = "▶ Run Episode";
                    log(`> Episode finished. Score: ${finalScore.toFixed(3)}`);
                    return;
                }
                const step = breakdown[i];
                const act = actions[step.action];
                
                if (step.action === 0 || step.action === 4) wear = 0;
                else wear += (step.action===3 ? 10 : step.action===2 ? 2.5 : 5);
                wear = Math.min(100, wear);

                if (step.action === 3) gap = Math.max(0, gap - 0.5);
                if (step.action === 2) gap += 0.5;

                document.getElementById("lap-display").textContent = step.lap;
                document.getElementById("wear-val").textContent = Math.round(wear) + "%";
                document.getElementById("gap-val").textContent = gap.toFixed(1) + "s";
                
                const bar = document.getElementById("tyre-bar");
                bar.style.width = wear + "%";
                if(wear < 50) bar.style.background = "var(--success)";
                else if(wear < 80) bar.style.background = "#f59e0b";
                else bar.style.background = "var(--danger)";

                let cls = "";
                if(step.action===0) cls="pit";
                if(step.action===3) cls="push";
                if(step.action===2) cls="conserve";

                log(`Lap ${step.lap} | Agent chose ${act} | Reward: ${step.reward.toFixed(2)}`, cls);

                const tb = document.createElement("div");
                tb.className = "time-bar";
                tb.style.height = Math.max(5, step.reward * 100) + "%";
                if(step.reward < 0.4) tb.style.background = "var(--danger)";
                else if(step.reward > 0.7) tb.style.background = "var(--success)";
                tb.setAttribute("data-val", step.reward.toFixed(2));
                timeline.appendChild(tb);

                i++;
            }, 100);
        }

        async function runMatrix() {
            const agents = ["easy", "medium", "hard", "conservative", "aggressive"];
            const phases = ["easy", "medium", "hard"];
            for(let a of agents) {
                for(let p of phases) {
                    const c = document.getElementById(`lb-${a}-${p}`);
                    c.textContent = "...";
                    c.style.color = "var(--text-muted)";
                    try {
                        const r = await fetch(`${API_BASE}/agents/${a}/run`, {
                            method:'POST',
                            headers:{'Content-Type':'application/json'},
                            body:JSON.stringify({task_id:p})
                        });
                        const data = await r.json();
                        c.textContent = data.score.toFixed(3);
                        c.style.color = data.score > 0.6 ? "var(--success)" : "var(--text)";
                    } catch(e) {}
                }
            }
        }
    </script>
</body>
</html>
"""

@app.get("/")
def root():
    return HTMLResponse(content=HTML_CONTENT)

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/metadata")
def metadata():
    return {"name": "gp-stratz", "description": "GP-Stratz running"}

@app.get("/schema")
def schema():
    return {
        "action": {
            "type": "integer",
            "description": "0=PIT, 1=STAY, 2=CONSERVE, 3=PUSH, 4=SWAP"
        },
        "observation": {
            "type": "object",
            "properties": {
                "lap_number": {"type": "integer"},
                "tyre_wear": {"type": "number"},
                "weather": {"type": "integer"},
                "gap_to_car": {"type": "number"},
                "safety_car": {"type": "boolean"},
                "traffic_level": {"type": "integer"},
                "tyre_deg_rate": {"type": "number"},
                "tyre_type": {"type": "integer"}
            }
        },
        "state": {"type": "object", "properties": {}}
    }

@app.get("/agents")
def list_agents():
    return [
        {
            "id": k,
            **v
        } for k, v in AGENT_META.items()
    ]

@app.get("/tasks")
def list_tasks():
    return TASKS

@app.get("/tasks/{task_id}/grade")
def grade_task(task_id: str):
    if task_id not in PHASE_SCENARIOS:
        raise HTTPException(status_code=404, detail="Unknown task")
    
    agent_id = task_id if task_id in AGENT_REGISTRY else "hard"
    agent = AGENT_REGISTRY[agent_id]()
    result = run_phase(task_id, agent)
    return {"task_id": task_id, "score": result["score"], "breakdown": result["breakdown_per_lap"]}

class ResetRequest(BaseModel):
    task_id: str = "easy"

@app.post("/reset")
async def reset(req: Optional[ResetRequest] = None):
    task_id = req.task_id if req else "easy"
    scenario = PHASE_SCENARIOS.get(task_id, {})
    obs = global_env.reset(scenario)
    return {"state": obs, "actions": {"0": "PIT", "1": "STAY", "2": "CONSERVE", "3": "PUSH", "4": "SWAP"}}

class StepRequest(BaseModel):
    action: int

@app.post("/step")
async def step(req: StepRequest):
    from agents.hard_agent import HardMultiFactorAgent
    oracle = HardMultiFactorAgent()
    optimal_action = oracle._get_optimal(global_env.state())
    obs, reward, done, info = global_env.step(req.action, optimal_action=optimal_action)
    return {"state": obs, "reward": reward, "done": done, "info": info}

class RunAgentRequest(BaseModel):
    task_id: str

@app.post("/agents/{agent_id}/run")
async def run_agent_on_phase(agent_id: str, req: RunAgentRequest):
    if agent_id not in AGENT_REGISTRY:
        raise HTTPException(status_code=404, detail="Unknown agent")
    if req.task_id not in PHASE_SCENARIOS:
        raise HTTPException(status_code=404, detail="Unknown task")
        
    agent = AGENT_REGISTRY[agent_id]()
    result = run_phase(req.task_id, agent, episodes=1)
    return result

def main():
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
