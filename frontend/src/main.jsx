// frontend/src/main.jsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

import CookieBanner from "./components/CookieBanner";
import { setupOptionalScripts } from "./lib/loaders.js";
setupOptionalScripts();

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
    {/* ✅ CookieBanner jen globálně, ne uvnitř App/Routes */}
    <CookieBanner />
  </React.StrictMode>
);
