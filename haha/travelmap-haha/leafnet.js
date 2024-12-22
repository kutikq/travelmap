// leafnet.js
document.addEventListener("DOMContentLoaded", function () {
    // Initialize map
    const map = L.map("map").setView([55.7558, 37.6173], 12);

    // Add OpenStreetMap tiles
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap contributors",
    }).addTo(map);
    
    // Add markers to the map
    locations.forEach(({ lat, lon, name }) => {
        const marker = L.marker([lat, lon]).addTo(map);
        marker.bindPopup(name);

        marker.on("click", function () {
            handlePlaceVisit(name);
        });
    });

    // Handle place visits and update progress
    const visitedPlaces = new Set();
    const totalPlaces = locations.length;
    const progressLabel = document.getElementById("progress-label");
    const rewardLabel = document.getElementById("reward-label");

    function handlePlaceVisit(placeName) {
        if (!visitedPlaces.has(placeName)) {
            visitedPlaces.add(placeName);
            updateProgress();
        }
    }

    function updateProgress() {
        const progress = (visitedPlaces.size / totalPlaces) * 100;
        progressLabel.textContent = `Прогресс: ${progress.toFixed(0)}%`;

        if (visitedPlaces.size >= 3) {
            rewardLabel.textContent = "Награда получена: Значок исследователя!";
        } else {
            rewardLabel.textContent = "";
        }
    }
});
