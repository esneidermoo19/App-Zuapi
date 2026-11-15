import { render, screen } from "@testing-library/react";
import App from "./App";

test("muestra el titulo principal", () => {
  render(<App />);
  expect(
    screen.getByRole("heading", { name: /conversor de archivos/i }),
  ).toBeInTheDocument();
});
