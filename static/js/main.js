function sortTable(n, tableId) {
    var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
    table = document.getElementById(tableId);
    if (!table) return; // Guard clause if table not found
    switching = true;
    dir = "asc";
    while (switching) {
        switching = false;
        rows = table.rows;
        for (i = 1; i < (rows.length - 1); i++) {
            shouldSwitch = false;
            x = rows[i].getElementsByTagName("TD")[n];
            y = rows[i + 1].getElementsByTagName("TD")[n];
            if (dir == "asc") {
                if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()) {
                    shouldSwitch = true;
                    break;
                }
            } else if (dir == "desc") {
                if (x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase()) {
                    shouldSwitch = true;
                    break;
                }
            }
        }
        if (shouldSwitch) {
            rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
            switching = true;
            switchcount++;
        } else {
            if (switchcount == 0 && dir == "asc") {
                dir = "desc";
                switching = true;
            }
        }
    }
}

// Modal Logic
function openModal(text) {
    var modal = document.getElementById("abstractModal");
    var modalText = document.getElementById("modalText");
    modalText.innerText = text;
    modal.style.display = "block";
}

function closeModal() {
    var modal = document.getElementById("abstractModal");
    modal.style.display = "none";
}

// Close modal when clicking outside of it
window.onclick = function (event) {
    var modal = document.getElementById("abstractModal");
    if (event.target == modal) {
        modal.style.display = "none";
    }
}

// Venn Diagram Logic
function drawVennDiagram(containerId, stats, labelA, labelB) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const { unique_a_count, overlap_count, unique_b_count, total_a, total_b } = stats;
    const total = unique_a_count + overlap_count + unique_b_count;

    // Percentages
    const pA = ((unique_a_count / (total || 1)) * 100).toFixed(1);
    const pO = ((overlap_count / (total || 1)) * 100).toFixed(1);
    const pB = ((unique_b_count / (total || 1)) * 100).toFixed(1);

    // Simple fixed layout for robustness, but we could make it proportional.
    // Let's use a nice reliable layout that looks good.
    // Viewbox 0 0 600 400
    // Center 300 200

    // Circle A center (200, 200), Radius 120
    // Circle B center (400, 200), Radius 120
    // Overlap is the middle.

    // This is a schematic view, not strictly area-proportional (which is hard to label nicely)
    // But we can scale radii slightly based on relative size if we want. 
    // Let's stick to a clean schematic for UI clarity as requested "numbers and percentage" is key.

    const svg = `
    <svg viewBox="0 0 600 350" style="width: 100%; height: auto; max-width: 600px;">
        <defs>
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
        </defs>
        
        <!-- Circle A (Left) -->
        <circle cx="220" cy="175" r="120" fill="var(--color-primary)" fill-opacity="0.2" stroke="var(--color-primary)" stroke-width="2" class="venn-circle" data-tooltip="Unique A: ${unique_a_count} (${pA}%)"/>
        
        <!-- Circle B (Right) -->
        <circle cx="380" cy="175" r="120" fill="var(--color-secondary)" fill-opacity="0.2" stroke="var(--color-secondary)" stroke-width="2" class="venn-circle" data-tooltip="Unique B: ${unique_b_count} (${pB}%)"/>
        
        <!-- Labels -->
        <text x="150" y="175" text-anchor="middle" fill="var(--color-text)" font-weight="bold" font-size="18">${unique_a_count}</text>
        <text x="150" y="200" text-anchor="middle" fill="var(--color-text-muted)" font-size="14">${pA}%</text>
        <text x="150" y="140" text-anchor="middle" fill="var(--color-primary)" font-size="16" font-weight="bold">${labelA}</text>

        <text x="450" y="175" text-anchor="middle" fill="var(--color-text)" font-weight="bold" font-size="18">${unique_b_count}</text>
        <text x="450" y="200" text-anchor="middle" fill="var(--color-text-muted)" font-size="14">${pB}%</text>
        <text x="450" y="140" text-anchor="middle" fill="var(--color-secondary)" font-size="16" font-weight="bold">${labelB}</text>
        
        <!-- Overlap Text -->
        <text x="300" y="175" text-anchor="middle" fill="var(--color-text)" font-weight="bold" font-size="20">${overlap_count}</text>
        <text x="300" y="200" text-anchor="middle" fill="var(--color-text-muted)" font-size="14">${pO}%</text>
        <text x="300" y="140" text-anchor="middle" fill="var(--color-accent)" font-size="14" font-weight="bold">Overlap</text>
        
        <!-- Tooltip foreignObject (simple version) or just title -->
        <title>Comparison Visualization</title>
    </svg>
    `;

    container.innerHTML = svg;

    // Add hover effects via JS or nice CSS
    // Let's rely on CSS for 'venn-circle' class
}
