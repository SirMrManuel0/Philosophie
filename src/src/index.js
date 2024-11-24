// src/templates/populated-worker/src/index.js
import html from "./static/preGame/teams.html"

var src_default = {
  async fetch(request, env) {
    /*const { DATABASE } = env;
    const stmt = DATABASE.prepare("SELECT * FROM comments LIMIT 3");
    const { results } = await stmt.all();*/

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