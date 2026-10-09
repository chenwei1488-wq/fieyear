export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    // 智能匹配 API 路径，无论部署在根目录还是子目录都能生效
    if (url.pathname.endsWith('/api/get-tk-id')) {
      const targetUrl = url.searchParams.get('url');
      const corsHeaders = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Content-Type": "application/json"
      };
      if (request.method === "OPTIONS") return new Response(null, { headers: corsHeaders });
      if (!targetUrl) return new Response(JSON.stringify({ error: "请提供 TikTok 链接" }), { status: 400, headers: corsHeaders });
      
      try {
        const response = await fetch(targetUrl, {
          method: 'GET',
          headers: {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
          },
          redirect: "follow"
        });
        const finalUrl = response.url;
        let videoId = null;
        let urlMatch = finalUrl.match(/\/video\/(\d+)/);
        if (urlMatch && urlMatch[1]) {
          videoId = urlMatch[1];
        } else {
          const htmlText = await response.text();
          const htmlMatch = htmlText.match(/\/video\/(\d+)/) || htmlText.match(/"aweme_id":"(\d+)"/) || htmlText.match(/"videoId":"(\d+)"/) || htmlText.match(/data-aweme-id="(\d+)"/);
          if (htmlMatch && htmlMatch[1]) videoId = htmlMatch[1];
        }
        if (videoId) return new Response(JSON.stringify({ success: true, videoId: videoId, finalUrl: finalUrl }), { status: 200, headers: corsHeaders });
        return new Response(JSON.stringify({ success: false, error: "未能提取到 ID", finalUrl: finalUrl }), { status: 404, headers: corsHeaders });
      } catch (error) {
        return new Response(JSON.stringify({ success: false, error: "请求错误: " + error.message }), { status: 500, headers: corsHeaders });
      }
    }
    return env.ASSETS.fetch(request);
  }
};