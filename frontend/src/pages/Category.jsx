import React from "react";
import { useParams } from "react-router-dom";
import Shop from "./Shop";

export default function CategoryPage() {
  const { slug } = useParams();
  return <Shop categorySlug={slug} />;
}
