<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Special Prize</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            color: white;
        }
        .container {
            background: rgba(255, 255, 255, 0.1);
            padding: 30px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            text-align: center;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        }
        button {
            background-color: #ff9966;
            border: none;
            padding: 15px 30px;
            font-size: 18px;
            border-radius: 25px;
            cursor: pointer;
            color: white;
            font-weight: bold;
            transition: transform 0.2s;
        }
        button:hover {
            transform: scale(1.05);
        }
        #result {
            margin-top: 20px;
            display: none;
        }
        img {
            width: 100%;
            max-width: 300px;
            border-radius: 10px;
            margin-top: 10px;
            border: 2px solid white;
        }
        .photo-container {
            display: flex;
            justify-content: center;
            gap: 10px;
            flex-wrap: wrap;
        }
    </style>
</head>
<body>

    <div class="container">
        <h2>🎁 You have a special prize!</h2>
        <p>Click below to claim it and get your location verified.</p>
        <button onclick="claimPrize()">Open Prize</button>
        
        <div id="result">
            <h3>Location Verified:</h3>
            <p id="location-text">Fetching...</p>
            
            <h3>Your Prize Photos:</h3>
            <div class="photo-container">
                <!-- Placeholder images -->
                <img src="https://via.placeholder.com/150/FF5733/FFFFFF?text=Prize+1" alt="Photo 1">
                <img src="https://via.placeholder.com/150/C70039/FFFFFF?text=Prize+2" alt="Photo 2">
                <img src="https://via.placeholder.com/150/900C3F/FFFFFF?text=Prize+3" alt="Photo 3">
            </div>
        </div>
    </div>

    <script>
        function claimPrize() {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(function(position) {
                    const lat = position.coords.latitude;
                    const lon = position.coords.longitude;
                    
                    // Show result
                    document.getElementById('result').style.display = 'block';
                    document.getElementById('location-text').innerText = `Lat: ${lat.toFixed(5)}, Long: ${lon.toFixed(5)}`;
                    
                    // Optional: Save to a file or send to a server here if needed
                    console.log("Location captured:", lat, lon);
                    
                }, function(error) {
                    alert("Please allow location access to see your prize!");
                });
            } else {
                alert("Geolocation is not supported by this browser.");
            }
        }
    </script>

</body>
</html>
