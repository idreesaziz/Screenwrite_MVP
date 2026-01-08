import { type RouteConfig, index, route } from "@react-router/dev/routes";

export default [
    // Public routes
    route("/auth/sign-in", "routes/SignIn.tsx"),
    
    // Protected routes (require authentication)
    route("/", "components/editor/auth/ProtectedRoute.tsx", [
        route("/", "routes/Home.tsx", [
            index("components/editor/timeline/MediaBin.tsx"),
            route("/properties", "components/editor/PropertiesPanel.tsx"),
            route("/transitions", "components/editor/media/Transitions.tsx"),
            route("/media-bin", "components/editor/redirects/mediaBinLoader.ts"),
        ]),
    ]),
    
    route("*", "./NotFound.tsx")
] satisfies RouteConfig;
