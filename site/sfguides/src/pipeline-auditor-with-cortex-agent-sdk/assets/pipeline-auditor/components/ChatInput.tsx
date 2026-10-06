"use client";

import { useState } from "react";
import {
  Box,
  TextField,
  IconButton,
  Paper,
  alpha,
  useTheme,
  Tooltip,
} from "@mui/material";
import { KeyboardArrowUp as SendIcon } from "@mui/icons-material";

interface ChatInputProps {
  onSend: (text: string) => void;
  disabled: boolean;
  placeholder?: string;
}

export function ChatInput({
  onSend,
  disabled,
  placeholder = "Ask a follow-up about any finding...",
}: ChatInputProps) {
  const theme = useTheme();
  const [text, setText] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (text.trim() && !disabled) {
      onSend(text.trim());
      setText("");
    }
  };

  return (
    <Paper
      elevation={0}
      sx={{
        p: 1.5,
        borderTop: `1px solid ${alpha(theme.palette.divider, 0.5)}`,
        bgcolor:
          theme.palette.mode === "dark"
            ? alpha(theme.palette.background.paper, 0.95)
            : theme.palette.background.paper,
      }}
    >
      <Box component="form" onSubmit={handleSubmit}>
        <Box sx={{ display: "flex", gap: 1, alignItems: "flex-end" }}>
          <TextField
            fullWidth
            multiline
            maxRows={3}
            size="small"
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
            placeholder={placeholder}
            disabled={disabled}
            sx={{
              "& .MuiOutlinedInput-root": {
                borderRadius: 1.5,
                fontSize: "0.9rem",
              },
            }}
          />
          <Tooltip title="Send (Cmd+Enter)" arrow>
            <span>
              <IconButton
                type="submit"
                color="primary"
                disabled={disabled || !text.trim()}
                sx={{
                  width: 40,
                  height: 40,
                  borderRadius: 1.5,
                  bgcolor: alpha(theme.palette.primary.main, 0.1),
                  "&:hover": {
                    bgcolor: alpha(theme.palette.primary.main, 0.2),
                  },
                  "&:disabled": {
                    bgcolor: alpha(theme.palette.action.disabled, 0.08),
                  },
                }}
              >
                <SendIcon />
              </IconButton>
            </span>
          </Tooltip>
        </Box>
      </Box>
    </Paper>
  );
}
