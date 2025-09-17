// frontend/src/main.jsx
import ReactDOM from "react-dom/client";
import { StrictMode } from "react";  // ✅ místo React importujeme jen StrictMode
import App from "./App.jsx";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
  </StrictMode>
);
