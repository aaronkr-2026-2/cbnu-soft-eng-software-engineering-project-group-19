import globals from "globals";

export default [
  {
    files: ["apps/web/**/*.js"],
    languageOptions: {
      sourceType: "script",
      globals: globals.browser,
    },
    rules: {
      "no-debugger": "error",
      "no-dupe-keys": "error",
      "no-undef": "error",
      "no-unreachable": "error",
      "no-unused-vars": ["error", { args: "after-used" }],
    },
  },
];
