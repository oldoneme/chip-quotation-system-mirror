import { useEffect, useState } from 'react';

const useIsMobile = (breakpoint = 768, initialValue = false) => {
  const [isMobile, setIsMobile] = useState(initialValue);

  useEffect(() => {
    const checkIsMobile = () => {
      setIsMobile(window.innerWidth <= breakpoint);
    };

    checkIsMobile();
    window.addEventListener('resize', checkIsMobile);

    return () => window.removeEventListener('resize', checkIsMobile);
  }, [breakpoint]);

  return isMobile;
};

export default useIsMobile;
