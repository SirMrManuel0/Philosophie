var __defProp = Object.defineProperty;
var __name = (target, value) => __defProp(target, "name", { value, configurable: true });

// src/templates/populated-worker/src/renderHtml.js
function renderHtml() {
  return `
    <!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Seite im Aufbau</title>
    <style>
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background-color: #121212;
            color: #ffffff;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            text-align: center;
        }
        .container {
            max-width: 600px;
        }
        h1 {
            font-size: 2.5rem;
            margin-bottom: 1rem;
        }
        p {
            font-size: 1.2rem;
            color: #bbbbbb;
        }
        .spinner {
            margin: 2rem auto;
            width: 50px;
            height: 50px;
            border: 5px solid #444;
            border-top: 5px solid #ffffff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Seite im Aufbau</h1>
        <div class="spinner"></div>
        <p>Wir arbeiten daran, diese Website bald verfügbar zu machen. Bitte schaue später wieder vorbei!</p>
    </div>
</body>
</html>

`;
}
__name(renderHtml, "renderHtml");
export {
  renderHtml as default
};
