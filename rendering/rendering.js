function renderGridToCanvas(grid, options = {}) {
    const canvas = document.getElementById("map");
    const ctx = canvas.getContext("2d");

    const h = grid.length;
    const w = grid[0].length;

    const tileSize = options.tileSize || Math.floor(
        Math.min(canvas.width / w, canvas.height / h)
    );

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    for (let y = 0; y < h; y++) {
        for (let x = 0; x < w; x++) {
            const cell = grid[y][x];

            // Adatta questa mappa ai tuoi valori reali
            let color = "#111";          // muro
            if (cell === 1) color = "#ddd";      // pavimento
            if (cell === 2) color = "#4caf50";   // stanza
            if (cell === 3) color = "#ff9800";   // corridoio

            ctx.fillStyle = color;
            ctx.fillRect(x * tileSize, y * tileSize, tileSize, tileSize);
        }
    }
}

let currentData = null;

async function loadMap(url) {
    const res = await fetch(url);
    currentData = await res.json();
    console.log("Caricata mappa da", url);
}

document.getElementById("btn-final").addEventListener("click", () => {
    if (!currentData || !currentData.meta || !currentData.meta.topo) return;
    renderGridToCanvas(currentData.meta.topo);
});

function animateSteps(steps, options = {}) {
    const delay = options.delay || 400;
    let index = 0;

    function next() {
        if (index >= steps.length) return;
        const step = steps[index];
        renderGridToCanvas(step.grid);
        index++;
        setTimeout(next, delay);
    }

    next();
}

document.getElementById("btn-animate").addEventListener("click", () => {
    if (!currentData || !currentData.steps) return;
    animateSteps(currentData.steps, { delay: 300 });
});

// Cambia l’URL con il tuo file/endpoint reale
loadMap("maps/bsp_125264467.json").then(() => {
    if (currentData && currentData.meta && currentData.meta.topo) {
        renderGridToCanvas(currentData.meta.topo);
    }
});

document.getElementById("btn-load").addEventListener("click", () => {
    const path = document.getElementById("map-select").value;

    loadMap(path).then(() => {
        renderGridToCanvas(currentData.meta.topo);
    });
});



