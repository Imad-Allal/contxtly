import React from "react";
import ReactDOM from "react-dom/client";
import { Scene1Hero, Scene2Save, Scene3Review, Scene4List, Scene5Settings, PromoTile } from "./scenes";

function App() {
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 32, padding: 32 }}>
      <Scene1Hero />
      <Scene2Save />
      <Scene3Review />
      <Scene4List />
      <Scene5Settings />
      <PromoTile />
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
