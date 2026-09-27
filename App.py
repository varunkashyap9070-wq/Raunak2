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
            text-align: center;
        }
        .container {
            background: rgba(255, 255, 255, 0.15);
            padding: 40px;
            border-radius: 20px;
            backdrop-filter: blur(10px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            width: 90%;
            max-width: 400px;
        }
        h2 { margin-bottom: 10px; }
        p { font-size: 14px; opacity: 0.9; }
        
        button {
            background: #ff9966;
            border: none;
            padding: 15px 30px;
            font-size: 18px;
            border-radius: 50px;
            color: white;
            font-weight: bold;
            cursor: pointer;
            margin-top: 20px;
            transition: 0.3s;
        }
        button:hover { background: #ff7f50; transform: scale(1.05); }
        
        #result { display: none; margin-top: 20px; }
        .photos {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 15px;
        }
        img {
            width: 100px;
            height: 100px;
            object-fit: cover;
            border-radius: 10px;
            border: 2px solid white;
        }
        .error { color: #ff6b6b; font-size: 12px; margin-top: 10px; }
    </style>
</head>
<body>

    <div class="container">
        <h2>🎁 You Won a Prize!</h2>
        <p>Click below to claim your reward and verify your location.</p>
        
        <button onclick="getLocation()">Claim Prize</button>
        
        <div id="result">
            <h3>✅ Verified!</h3>
            <p id="location-text">Fetching...</p>
            
            <div class="photos">
                <img src="https://via.placeholder.com/150/FF5733/FFFFFF?text=Prize+1" alt="Prize 1">
                <img src="https://via.placeholder.com/150/C70039/FFFFFF?text=Prize+2" alt="Prize 2">
                <img src="https://via.placeholder.com/150/900C3F/FFFFFF?text=Prize+3" alt="Prize 3">
            </div>
            <p style="font-size: 10px; margin-top: 10px;">Location data captured successfully.</p>
        </div>
        <div id="error-msg" class="error"></div>
    </div>

    <script>
        function getLocation() {
            const btn = document.querySelector('button');
            const resultDiv = document.getElementById('result');
            const errDiv = document.getElementById('error-msg');
            
            btn.disabled = true;
            btn.innerText = "Verifying...";
            errDiv.innerText = "";

            if (!navigator.geolocation) {
                errDiv.innerText = "Geolocation is not supported by your browser.";
                btn.disabled = false;
                btn.innerText = "Try Again";
                return;
            }

            navigator.geolocation.getCurrentPosition(
                (position) => {
                    // Success
                    const lat = position.coords.latitude.toFixed(5);
                    const lon = position.coords.longitude.toFixed(5);
                    
                    document.getElementById('location-text').innerText = 
                        `Location: ${lat}, ${lon}`;
                    
                    resultDiv.style.display = 'block';
                    btn.style.display = 'none';
                },
                (error) => {
                    // Error
                    let msg = "Unknown error.";
                    switch(error.code) {
                        case error.PERMISSION_DENIED:
                            msg = "Location access denied. Please allow location and click again.";
                            break;
                        case error.POSITION_UNAVAILABLE:
                            msg = "Location information unavailable.";
                            break;
                        case error.TIMEOUT:
                            msg = "Location request timed out.";
                            break;
                    }
                    errDiv.innerText = msg;
                    btn.disabled = false;
                    btn.innerText = "Try Again";
                },
                { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
            );
        }
    </script>

</body>
</html>
