import React from "react";
import { Routes, Route } from "react-router-dom";
import HomePage from "./HomePage";

const App = () => {
  return (
    <>
      <main>
        <Routes>
          <Route path="/" element={<HomePage />} />
        </Routes>
      </main>
    </>
  );
};

export default App;
