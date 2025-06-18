import React from "react";

export default function Navbar() {
  return (
    <nav className="absolute top-0 left-0 w-full z-20 px-8 py-4 text-pink-900">
      <div className="flex justify-between items-center max-w-7xl mx-auto">
        <div className="text-2xl font-bold tracking-wider">
          <a href="#">Náramková Móda</a>
        </div>
        <ul className="flex space-x-6 text-lg font-medium">
          <li><a href="#home" className="hover:text-pink-600">Domů</a></li>
          <li><a href="#gallery" className="hover:text-pink-600">Galerie</a></li>
        </ul>
      </div>
    </nav>
  );
}
