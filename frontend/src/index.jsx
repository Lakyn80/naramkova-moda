// ✅ Export hlavní třídy widgetu jako `window.ChatWidget`
import ChatWidget from "./components/ChatWidget";

// 🟢 Zajistí, že bude dostupné přes <script> → window.ChatWidget.init()
window.ChatWidget = ChatWidget;
