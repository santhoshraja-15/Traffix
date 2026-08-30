import { redirect } from "next/navigation";

// This route previously rendered nothing at all (an empty "TODO: implement"
// stub — a real dead end at /navigation, not a 404). The real navigation
// experience lives at the app root; redirect there rather than leave a
// blank page reachable by URL.
export default function NavigationPage() {
  redirect("/");
}
