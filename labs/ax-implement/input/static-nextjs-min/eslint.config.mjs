import next from "eslint-config-next";

export default [
  ...next,
  {
    rules: {
      "no-restricted-syntax": [
        "error",
        {
          selector: "Literal[value=/^[가-힣A-Z].*[가-힣a-z]$/]",
          message: "UI 텍스트는 i18n 경유 (src/i18n/copy.ts)",
        },
      ],
    },
  },
];
