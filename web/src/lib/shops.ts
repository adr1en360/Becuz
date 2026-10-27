// Fictional names for the five synthetic test weeks (data/scenarios/s01 to s05), so testers pick a shop, not a code.
// The names and initials logos are made up for testing; no real business is meant.
export const TEST_SHOPS = [
  { id: "s01", name: "Adaeze Mini Mart", initials: "AM", colour: "#ff7a3d", hint: "Several things went wrong at once" },
  { id: "s02", name: "Kola Provisions", initials: "KP", colour: "#d4a24c", hint: "A supplier raised a price" },
  { id: "s03", name: "Ebun Superstore", initials: "ES", colour: "#7fa7e0", hint: "A promo overran and stock was wasted" },
  { id: "s04", name: "Musa Corner Shop", initials: "MC", colour: "#e4b2a0", hint: "Sales are fine, but money is missing" },
  { id: "s05", name: "Ngozi Fresh Mart", initials: "NF", colour: "#9fc9a8", hint: "A normal week, nothing wrong" },
] as const;

export const shopName = (id: string | null | undefined) => TEST_SHOPS.find((s) => s.id === id)?.name ?? id ?? "";
