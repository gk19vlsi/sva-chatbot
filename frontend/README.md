# SVA-Chatbot Frontend

React + TypeScript frontend for the SVA-Chatbot system.

## Setup

### Install Dependencies

```bash
# Using npm
npm install

# Using yarn
yarn install
```

### Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
```

### Development

```bash
# Start development server
npm run dev
# or
yarn dev

# Visit http://localhost:3000
```

### Build

```bash
# Build for production
npm run build
# or
yarn build

# Preview production build
npm run preview
# or
yarn preview
```

## Project Structure

```
frontend/
├── src/
│   ├── main.tsx         # Application entry point
│   ├── App.tsx          # Root component
│   ├── index.css        # Global styles
│   ├── components/      # React components
│   ├── contexts/        # React contexts
│   ├── hooks/           # Custom hooks
│   ├── services/        # API services
│   ├── types/           # TypeScript types
│   └── utils/           # Utility functions
├── public/              # Static assets
├── index.html           # HTML template
├── package.json         # Dependencies
├── tsconfig.json        # TypeScript config
├── vite.config.ts       # Vite config
└── tailwind.config.js   # Tailwind CSS config
```

## Technologies

- React 18
- TypeScript
- Vite
- Tailwind CSS
- React Router
- Monaco Editor
- Recharts
- Axios
