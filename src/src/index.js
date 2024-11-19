// src/templates/populated-worker/src/index.js
import renderHtml from "./renderHtml.js";
var src_default = {
  async fetch(request, env) {
    const { DATABASE } = env;
    const stmt = DATABASE.prepare("SELECT * FROM comments LIMIT 3");
    const { results } = await stmt.all();
    return new Response(
      renderHtml(JSON.stringify(results, null, 2)),
      {
        headers: {
          "content-type": "text/html"
        }
      }
    );
  }
};
export {
  src_default as default
};
