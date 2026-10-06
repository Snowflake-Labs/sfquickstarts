import { createTheme, type PaletteMode } from "@mui/material/styles";

export function getTheme(mode: PaletteMode) {
  return createTheme({
    palette: {
      mode,
      primary: {
        main: "#667eea",
        light: "#8fa4f0",
        dark: "#4a5fc7",
      },
      secondary: {
        main: "#764ba2",
        light: "#9b6fc4",
        dark: "#5a3480",
      },
      background:
        mode === "dark"
          ? { default: "#0f1117", paper: "#1a1d2e" }
          : { default: "#f5f5f9", paper: "#ffffff" },
      error: { main: "#f44336" },
      warning: { main: "#ff9800" },
      success: { main: "#4caf50" },
      info: { main: "#2196f3" },
      divider:
        mode === "dark"
          ? "rgba(255,255,255,0.08)"
          : "rgba(0,0,0,0.08)",
    },
    typography: {
      fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
      h5: { fontWeight: 700 },
      h6: { fontWeight: 600 },
      subtitle1: { fontWeight: 600 },
      subtitle2: { fontWeight: 600 },
    },
    shape: {
      borderRadius: 8,
    },
    components: {
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundImage: "none",
          },
        },
      },
      MuiAccordion: {
        styleOverrides: {
          root: {
            backgroundImage: "none",
          },
        },
      },
    },
  });
}
