import React from 'react';
import { cache } from '../utils/cache';
import { api } from '../services/apiClient';

interface DocREDSample {
  index: number;
  goal: string;
  text_preview: string;
  text_length: number;
  sentence_count: number;
  entity_count: number;
  relation_count: number;
}

interface DocREDBrowserProps {
  onSelect: (payload: {
    goal: string;
    text: string;
    datasetRef: { datasetId: string; split: string; index: number };
  }) => void;
  onClose: () => void;
}

export default function DocREDBrowser({ onSelect, onClose }: DocREDBrowserProps) {
  const [files, setFiles] = React.useState<any[]>([]);
  const [selectedFile, setSelectedFile] = React.useState<string>('');
  const [samples, setSamples] = React.useState<DocREDSample[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [page, setPage] = React.useState(1);
  const [totalPages, setTotalPages] = React.useState(1);
  const [selectedSample, setSelectedSample] = React.useState<DocREDSample | null>(null);
  const [sampleDetail, setSampleDetail] = React.useState<any>(null);
  const [loadingDetail, setLoadingDetail] = React.useState(false);
  const [filesError, setFilesError] = React.useState<string | null>(null);

  // 加载文件列表（带缓存）
  React.useEffect(() => {
    setFilesError(null);
    
    // 先尝试从缓存加载
    const cachedFiles = cache.files.get();
    if (cachedFiles && cachedFiles.length > 0) {
      console.log('Loading files from cache');
      setFiles(cachedFiles);
      const validFiles = cachedFiles.filter((f: any) => f.count !== undefined);
      if (validFiles.length > 0) {
        setSelectedFile(validFiles[0].name);
      }
    }
    
    // 同时从 API 加载（更新缓存）
    api.docred.files()
      .then((data: any) => {
        console.log('DocRED files response:', data);
        const filesList = data.files || [];
        
        // 更新缓存
        if (filesList.length > 0) {
          cache.files.set(filesList);
        }
        
        setFiles(filesList);
        
        if (filesList.length > 0) {
          // 只选择有 count 的文件（成功加载的文件）
          const validFiles = filesList.filter((f: any) => f.count !== undefined);
          if (validFiles.length > 0) {
            setSelectedFile(validFiles[0].name);
          } else {
            setFilesError('找到文件但无法加载数据，请检查文件格式');
          }
        } else {
          const errorMsg = data.error || '未找到 DocRED 数据文件';
          setFilesError(`${errorMsg} (目录: ${data.data_dir || '未知'})`);
        }
      })
      .catch(err => {
        console.error('Error loading files:', err);
        // 如果缓存中有数据，继续使用缓存
        if (!cachedFiles || cachedFiles.length === 0) {
          setFilesError(`无法连接到 API: ${err.message}。请确保 Python 服务正在运行`);
          setFiles([]);
        }
      });
  }, []);

  // 加载样本列表（带缓存）
  React.useEffect(() => {
    if (!selectedFile) return;
    
    // 先尝试从缓存加载
    const cachedSamples = cache.samples.get(selectedFile, page);
    if (cachedSamples) {
      console.log(`Loading samples from cache: ${selectedFile} page ${page}`);
      setSamples(cachedSamples.samples || []);
      setTotalPages(cachedSamples.total_pages || 1);
      setLoading(false);
    } else {
      setLoading(true);
    }
    
    // 同时从 API 加载（更新缓存）
    api.docred.samples(selectedFile, page, 20)
      .then((data: any) => {
        // 更新缓存
        cache.samples.set(selectedFile, page, data);
        
        setSamples(data.samples || []);
        setTotalPages(data.total_pages || 1);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error loading samples:', err);
        // 如果缓存中有数据，继续使用缓存
        if (!cachedSamples) {
          setLoading(false);
        }
      });
  }, [selectedFile, page]);

  // 加载样本详情（带缓存）
  const loadSampleDetail = async (sample: DocREDSample) => {
    setSelectedSample(sample);
    
    // 先尝试从缓存加载
    const cachedDetail = cache.sampleDetail.get(selectedFile, sample.index);
    if (cachedDetail) {
      console.log(`Loading sample detail from cache: ${selectedFile} index ${sample.index}`);
      setSampleDetail(cachedDetail);
      setLoadingDetail(false);
    } else {
      setLoadingDetail(true);
    }
    
    // 同时从 API 加载（更新缓存）
    try {
      const data = await api.docred.sample(selectedFile, sample.index);
      
      // 更新缓存
      cache.sampleDetail.set(selectedFile, sample.index, data);
      
      setSampleDetail(data);
    } catch (err) {
      console.error('Error loading sample detail:', err);
      // 如果缓存中有数据，继续使用缓存
      if (!cachedDetail) {
        setLoadingDetail(false);
      }
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleSelect = () => {
    if (sampleDetail) {
      onSelect({
        goal: sampleDetail.goal,
        text: sampleDetail.text,
        datasetRef: { datasetId: 'docred', split: selectedFile, index: sampleDetail.index },
      });
      onClose();
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      zIndex: 1000,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '8px',
        width: '90%',
        maxWidth: '1200px',
        maxHeight: '90vh',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'
      }}>
        {/* 头部 */}
        <div style={{
          padding: '20px',
          borderBottom: '1px solid #ccc',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <h2 style={{ margin: 0 }}>浏览 DocRED 数据集</h2>
          <button
            onClick={onClose}
            style={{
              padding: '8px 16px',
              border: '1px solid #ccc',
              borderRadius: '4px',
              backgroundColor: 'white',
              cursor: 'pointer'
            }}
          >
            关闭
          </button>
        </div>

        {/* 内容区域 */}
        <div style={{
          display: 'flex',
          flex: 1,
          overflow: 'hidden'
        }}>
          {/* 左侧：文件列表和样本列表 */}
          <div style={{
            width: '400px',
            borderRight: '1px solid #ccc',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden'
          }}>
            {/* 文件选择 */}
            <div style={{ padding: '15px', borderBottom: '1px solid #ccc' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
                选择数据文件：
              </label>
              {filesError ? (
                <div style={{
                  padding: '10px',
                  backgroundColor: '#f8d7da',
                  border: '1px solid #dc3545',
                  borderRadius: '4px',
                  fontSize: '12px',
                  color: '#721c24'
                }}>
                  <div style={{ marginBottom: '5px', fontWeight: 'bold' }}>❌ 错误</div>
                  <div style={{ fontSize: '11px' }}>{filesError}</div>
                </div>
              ) : files.length === 0 ? (
                <div style={{
                  padding: '10px',
                  backgroundColor: '#fff3cd',
                  border: '1px solid #ffc107',
                  borderRadius: '4px',
                  fontSize: '12px',
                  color: '#856404'
                }}>
                  <div style={{ marginBottom: '5px' }}>⚠️ 加载中...</div>
                </div>
              ) : (
                <select
                  value={selectedFile}
                  onChange={(e) => {
                    setSelectedFile(e.target.value);
                    setPage(1);
                  }}
                  style={{
                    width: '100%',
                    padding: '8px',
                    border: '1px solid #ccc',
                    borderRadius: '4px'
                  }}
                >
                  {files.map(file => (
                    <option key={file.name} value={file.name}>
                      {file.name} ({file.count || 0} 样本)
                    </option>
                  ))}
                </select>
              )}
            </div>

            {/* 样本列表 */}
            <div style={{ flex: 1, overflow: 'auto', padding: '10px' }}>
              {loading ? (
                <div style={{ textAlign: 'center', padding: '20px' }}>加载中...</div>
              ) : (
                <>
                  {samples.map(sample => (
                    <div
                      key={sample.index}
                      onClick={() => loadSampleDetail(sample)}
                      style={{
                        padding: '12px',
                        marginBottom: '8px',
                        border: selectedSample?.index === sample.index 
                          ? '2px solid #007bff' 
                          : '1px solid #ddd',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        backgroundColor: selectedSample?.index === sample.index 
                          ? '#e7f3ff' 
                          : 'white'
                      }}
                    >
                      <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>
                        样本 #{sample.index}
                      </div>
                      <div style={{ fontSize: '12px', color: '#666', marginBottom: '5px' }}>
                        {sample.text_preview}
                      </div>
                      <div style={{ fontSize: '11px', color: '#999' }}>
                        句子: {sample.sentence_count} | 
                        实体: {sample.entity_count} | 
                        关系: {sample.relation_count} | 
                        长度: {sample.text_length}
                      </div>
                    </div>
                  ))}
                  
                  {/* 分页 */}
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginTop: '15px',
                    padding: '10px'
                  }}>
                    <button
                      onClick={() => setPage(p => Math.max(1, p - 1))}
                      disabled={page === 1}
                      style={{
                        padding: '6px 12px',
                        border: '1px solid #ccc',
                        borderRadius: '4px',
                        backgroundColor: page === 1 ? '#f5f5f5' : 'white',
                        cursor: page === 1 ? 'not-allowed' : 'pointer'
                      }}
                    >
                      上一页
                    </button>
                    <span style={{ fontSize: '14px' }}>
                      第 {page} / {totalPages} 页
                    </span>
                    <button
                      onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                      disabled={page === totalPages}
                      style={{
                        padding: '6px 12px',
                        border: '1px solid #ccc',
                        borderRadius: '4px',
                        backgroundColor: page === totalPages ? '#f5f5f5' : 'white',
                        cursor: page === totalPages ? 'not-allowed' : 'pointer'
                      }}
                    >
                      下一页
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* 右侧：样本详情 */}
          <div style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden'
          }}>
            {loadingDetail ? (
              <div style={{ padding: '40px', textAlign: 'center' }}>加载详情中...</div>
            ) : sampleDetail ? (
              <>
                <div style={{
                  padding: '20px',
                  borderBottom: '1px solid #ccc',
                  overflow: 'auto',
                  flex: 1
                }}>
                  <h3 style={{ marginTop: 0 }}>样本详情</h3>
                  
                  <div style={{ marginBottom: '15px' }}>
                    <strong>目标 (Goal):</strong>
                    <div style={{
                      padding: '10px',
                      backgroundColor: '#f9f9f9',
                      borderRadius: '4px',
                      marginTop: '5px'
                    }}>
                      {sampleDetail.goal}
                    </div>
                  </div>

                  <div style={{ marginBottom: '15px' }}>
                    <strong>文本内容 (Text):</strong>
                    <div style={{
                      padding: '10px',
                      backgroundColor: '#f9f9f9',
                      borderRadius: '4px',
                      marginTop: '5px',
                      maxHeight: '300px',
                      overflow: 'auto',
                      whiteSpace: 'pre-wrap',
                      fontSize: '14px',
                      lineHeight: '1.6'
                    }}>
                      {sampleDetail.text}
                    </div>
                  </div>

                  <div style={{ marginBottom: '15px' }}>
                    <strong>统计信息:</strong>
                    <ul style={{ margin: '5px 0', paddingLeft: '20px' }}>
                      <li>句子数: {sampleDetail.metadata?.sentence_count || 0}</li>
                      <li>实体数: {sampleDetail.metadata?.entity_count || 0}</li>
                      <li>关系数: {sampleDetail.metadata?.relation_count || 0}</li>
                      <li>文本长度: {sampleDetail.text?.length || 0} 字符</li>
                    </ul>
                  </div>
                </div>

                <div style={{
                  padding: '15px',
                  borderTop: '1px solid #ccc',
                  display: 'flex',
                  justifyContent: 'flex-end',
                  gap: '10px'
                }}>
                  <button
                    onClick={onClose}
                    style={{
                      padding: '10px 20px',
                      border: '1px solid #ccc',
                      borderRadius: '4px',
                      backgroundColor: 'white',
                      cursor: 'pointer'
                    }}
                  >
                    取消
                  </button>
                  <button
                    onClick={handleSelect}
                    style={{
                      padding: '10px 20px',
                      border: 'none',
                      borderRadius: '4px',
                      backgroundColor: '#007bff',
                      color: 'white',
                      cursor: 'pointer',
                      fontWeight: 'bold'
                    }}
                  >
                    使用此数据
                  </button>
                </div>
              </>
            ) : (
              <div style={{
                padding: '40px',
                textAlign: 'center',
                color: '#999'
              }}>
                请从左侧选择一个样本
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
