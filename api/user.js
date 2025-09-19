export default function handler(request, response) {
  // ���� Vercel ר�����棨1Сʱ��
  response.setHeader('Vercel-CDN-Cache-Control', 'max-age=3600');
  // �������� CDN ���棨1���ӣ�
  response.setHeader('CDN-Cache-Control', 'max-age=60');
  // ������������棨10�룩
  response.setHeader('Cache-Control', 'max-age=10');

  // ��������
  return response.status(200).json({ 
    name: 'John Doe',
    updatedAt: new Date().toISOString()
  });
}
