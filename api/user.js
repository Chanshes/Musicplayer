export default function handler(request, response) {
  // 配置 Vercel 专属缓存（1小时）
  response.setHeader('Vercel-CDN-Cache-Control', 'max-age=3600');
  // 配置其他 CDN 缓存（1分钟）
  response.setHeader('CDN-Cache-Control', 'max-age=60');
  // 配置浏览器缓存（10秒）
  response.setHeader('Cache-Control', 'max-age=10');

  // 返回数据
  return response.status(200).json({ 
    name: 'John Doe',
    updatedAt: new Date().toISOString()
  });
}
