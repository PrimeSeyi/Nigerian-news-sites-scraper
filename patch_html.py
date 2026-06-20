import re

with open("dashboard_viewer/index.html", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update CSS
css_addition = """
        .zone-header {
            background-color: #2a2a2a;
            color: var(--primary-color);
            padding: 12px 15px;
            margin-top: 10px;
            margin-bottom: 5px;
            cursor: pointer;
            font-weight: bold;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .zone-header:hover {
            background-color: #333;
        }
        .zone-content {
            display: none;
            padding-left: 15px;
            border-left: 2px solid #333;
            margin-left: 10px;
        }
        .zone-content.open {
            display: block;
        }
        .broad-regions-header {
            margin-top: 25px;
            color: var(--secondary-color);
            font-size: 1.2em;
            border-bottom: 1px solid #333;
            padding-bottom: 5px;
        }
"""
# inject before /* Main content area */
content = content.replace("        /* Main content area */", css_addition + "        /* Main content area */")


# 2. Rewrite initDashboard
old_init = """        function initDashboard() {
            const stateList = document.getElementById('state-list');
            stateList.innerHTML = '';
            
            // Render states
            const states = Object.keys(dashboardData.states);
            
            // Add an 'All States' button
            const allBtn = document.createElement('button');
            allBtn.className = 'state-btn active';
            allBtn.innerHTML = `All Locations <span class="badge">${dashboardData.metadata.total_clusters}</span>`;
            allBtn.onclick = () => {
                document.querySelectorAll('.state-btn').forEach(b => b.classList.remove('active'));
                allBtn.classList.add('active');
                renderState('All Locations');
            }
            stateList.appendChild(allBtn);

            states.forEach(state => {
                const btn = document.createElement('button');
                btn.className = 'state-btn';
                btn.innerHTML = `${state} <span class="badge">${dashboardData.states[state].total_clusters}</span>`;
                btn.onclick = (e) => {
                    document.querySelectorAll('.state-btn').forEach(b => b.classList.remove('active'));
                    e.currentTarget.classList.add('active');
                    renderState(state);
                };
                stateList.appendChild(btn);
            });
            
            renderState('All Locations');
        }"""

new_init = """        const ZONE_MAPPING = {
            "North West": ["Kaduna", "Kano", "Katsina", "Kebbi", "Jigawa", "Sokoto", "Zamfara"],
            "North East": ["Adamawa", "Bauchi", "Borno", "Gombe", "Taraba", "Yobe"],
            "North Central": ["Benue", "Kogi", "Kwara", "Nasarawa", "Niger", "Plateau", "FCT"],
            "South West": ["Ekiti", "Lagos", "Ogun", "Ondo", "Osun", "Oyo"],
            "South East": ["Abia", "Anambra", "Ebonyi", "Enugu", "Imo"],
            "South South": ["Akwa Ibom", "Bayelsa", "Cross River", "Delta", "Edo", "Rivers"]
        };

        const BROAD_REGIONS = ["The North", "The South", "The East", "The West", "Middle Belt", "Unresolved Region"];

        function createButton(label, actualStateKey) {
            const data = dashboardData.states[actualStateKey];
            if (!data) return null; // State has no incidents
            
            const btn = document.createElement('button');
            btn.className = 'state-btn';
            btn.innerHTML = `${label} <span class="badge">${data.total_clusters}</span>`;
            btn.onclick = (e) => {
                document.querySelectorAll('.state-btn').forEach(b => b.classList.remove('active'));
                e.currentTarget.classList.add('active');
                renderState(actualStateKey);
            };
            return btn;
        }

        function initDashboard() {
            const stateList = document.getElementById('state-list');
            stateList.innerHTML = '';
            
            const allBtn = document.createElement('button');
            allBtn.className = 'state-btn active';
            allBtn.innerHTML = `All Locations <span class="badge">${dashboardData.metadata.total_clusters}</span>`;
            allBtn.onclick = () => {
                document.querySelectorAll('.state-btn').forEach(b => b.classList.remove('active'));
                allBtn.classList.add('active');
                renderState('All Locations');
            }
            stateList.appendChild(allBtn);

            // Create Accordion for Zones
            for (const [zone, states] of Object.entries(ZONE_MAPPING)) {
                // Check if zone or its states have any data at all
                const hasData = dashboardData.states[zone] || states.some(s => dashboardData.states[s]);
                if (!hasData) continue;

                // Create Accordion Header
                const header = document.createElement('div');
                header.className = 'zone-header';
                header.innerHTML = `<span>${zone} Zone</span> <span class="toggle-icon">▼</span>`;
                
                // Create Accordion Content Container
                const content = document.createElement('div');
                content.className = 'zone-content';
                
                // Toggle Logic
                header.onclick = () => {
                    content.classList.toggle('open');
                    header.querySelector('.toggle-icon').innerText = content.classList.contains('open') ? '▲' : '▼';
                };
                
                stateList.appendChild(header);
                stateList.appendChild(content);

                // 1. Add General Zone Button (if incidents exist for the broad zone)
                const generalBtn = createButton(`General ${zone}`, zone);
                if (generalBtn) content.appendChild(generalBtn);

                // 2. Add Specific States under this zone
                states.forEach(state => {
                    const stateBtn = createButton(state, state);
                    if (stateBtn) content.appendChild(stateBtn);
                });
            }

            // Create Broad Regions section at the bottom
            const broadHeader = document.createElement('div');
            broadHeader.className = 'broad-regions-header';
            broadHeader.innerText = 'Broad Regions & Unresolved';
            stateList.appendChild(broadHeader);

            BROAD_REGIONS.forEach(region => {
                const btn = createButton(region, region);
                if (btn) stateList.appendChild(btn);
            });
            
            renderState('All Locations');
        }"""

content = content.replace(old_init, new_init)

with open("dashboard_viewer/index.html", "w", encoding="utf-8") as f:
    f.write(content)

print("Updated HTML with Accordion UI")
