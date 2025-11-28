import React, { useState } from "react";
import { Sidebar } from "./components/Sidebar";
import { TopBar } from "./components/TopBar";
import { ProductManagement } from "./components/ProductManagement";
import { HighRevenueShopsReport } from "./components/HighRevenueShopsReport";

export default function App() {
  const [currentPage, setCurrentPage] = useState<"products" | "revenue-report">(
    "products"
  );

  return (
    <div className="flex h-screen bg-[#F5F5F5]">
      <Sidebar currentPage={currentPage} onNavigate={setCurrentPage} />
      <div className="flex-1 flex flex-col overflow-hidden ml-64">
        <TopBar currentPage={currentPage} />
        <main className="flex-1 overflow-y-auto p-6 mt-16">
          {currentPage === "products" ? (
            <ProductManagement />
          ) : (
            <HighRevenueShopsReport />
          )}
        </main>
      </div>
    </div>
  );
}
