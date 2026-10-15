/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#231d17',        // body text, primary buttons
        soft: '#6f6253',       // secondary text
        line: '#e4d9c9',       // hairlines
        paper: '#f6f1e8',      // page ground (paper bag interior)
        card: '#fffdf8',       // raised surfaces
        kraft: '#a86f37',      // the brown-bag accent
        kraftdeep: '#7d4f22',
        moss: '#3f6b4a',       // success, approved
        rust: '#b4462f',       // problems
        sky: '#3d6a8a',        // info
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'system-ui', '-apple-system', 'Segoe UI', 'Helvetica', 'Arial', 'sans-serif'],
        serif: ['Newsreader', 'Georgia', '"Times New Roman"', 'serif'],
      },
      maxWidth: { prose: '65ch' },
    },
  },
  plugins: [],
}
