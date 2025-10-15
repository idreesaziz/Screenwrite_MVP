import { type RouteConfig, index, route } from "@react-router/dev/routes";

export default [
    // Public routes
    route("/auth/sign-in", "routes/auth.sign-in.tsx"),
    
    // Protected routes (require authentication)
    route("/", "components/auth/ProtectedRoute.tsx", [
        route("/", "routes/home.tsx", [
            index("components/timeline/MediaBin.tsx"),
            route("/properties", "components/editor/PropertiesPanel.tsx"),
            route("/transitions", "components/media/Transitions.tsx"),
            route("/media-bin", "components/redirects/mediaBinLoader.ts"),
        ]),
        route("/learn", "routes/learn.tsx"),
        route("/test", "routes/test.tsx"),
    ]),
    
    route("*", "./NotFound.tsx")
] satisfies RouteConfig;
