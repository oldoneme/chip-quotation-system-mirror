import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const useKeyboardShortcuts = () => {
  const navigate = useNavigate();

  useEffect(() => {
    const handleKeyPress = (event) => {
      // 只在没有焦点在输入框时响应快捷键
      const isInputFocused = document.activeElement.tagName === 'INPUT' || 
                            document.activeElement.tagName === 'TEXTAREA' ||
                            document.activeElement.contentEditable === 'true';
      
      if (isInputFocused) return;

      // Ctrl/Cmd + 数字键的快捷方式
      if ((event.ctrlKey || event.metaKey) && !event.shiftKey && !event.altKey) {
        switch(event.key) {
          case '1':
            event.preventDefault();
            navigate('/');
            break;
          case '2':
            event.preventDefault();
            navigate('/engineering-quote');
            break;
          case '3':
            event.preventDefault();
            navigate('/mass-production-quote');
            break;
          case '4':
            event.preventDefault();
            navigate('/hierarchical-database-management');
            break;
          case '5':
            event.preventDefault();
            navigate('/api-test');
            break;
          default:
            break;
        }
      }
      
      // ESC键返回首页
      if (event.key === 'Escape') {
        navigate('/');
      }
    };

    document.addEventListener('keydown', handleKeyPress);

    return () => {
      document.removeEventListener('keydown', handleKeyPress);
    };
  }, [navigate]);
};

export default useKeyboardShortcuts;