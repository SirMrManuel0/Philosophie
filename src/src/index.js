// src/templates/populated-worker/src/index.js
import html from "./static/pre_game/teams.html"


var src_default = {
  async fetch(request, env) {
    /*const { DATABASE } = env;
    const stmt = DATABASE.prepare("SELECT * FROM comments LIMIT 3");
    const { results } = await stmt.all();*/

    let url = String(request.url);

    if (url.startsWith("https://philosophie.tcku.dev/static")) {
      return staticHandler(request);
    }

    // Standard-Route: HTML-Seite rendern
    return new Response(html, {
      headers: { "Content-Type": "text/html" },
    });
  }
};
export {
  src_default as default
};
//test