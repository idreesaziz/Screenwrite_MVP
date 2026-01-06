import { type RouteConfig, index, route } from "@react-router/dev/routes";

export default [
    // Public routes
    route("/auth/sign-in", "routes/auth.sign-in.tsx"),
    
    // Protected routes (require authentication)
    route("/", "components/editor/auth/ProtectedRoute.tsx", [
        route("/", "routes/home.tsx", [
            index("components/editor/timeline/MediaBin.tsx"),
            route("/properties", "components/editor/PropertiesPanel.tsx"),
            route("/transitions", "components/editor/media/Transitions.tsx"),
            route("/media-bin", "components/editor/redirects/mediaBinLoader.ts"),
        ]),
        route("/learn", "routes/learn.tsx"),
        route("/test", "routes/test.tsx"),
    ]),
    
    route("*", "./NotFound.tsx")
] satisfies RouteConfig;
