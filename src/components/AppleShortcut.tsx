import { Smartphone } from "lucide-react";
import { Button } from "./ui/button";
import { useTranslation } from "react-i18next";

export const AppleShortcut = () => {
  const { t } = useTranslation();
  
  return (
    <div className="mt-16 flex flex-col items-center gap-6 w-full max-w-md mx-auto px-4">
      <a 
        href="https://www.icloud.com/shortcuts/e15b5336eba049e6a220f23e0900005e"
        target="_blank"
        rel="noopener noreferrer"
        className="w-full flex justify-center"
      >
        <Button 
          className="bg-black hover:bg-gray-800 text-white border-none w-full md:w-auto md:min-w-[240px] h-11"
        >
          {t('getOne')} iPhone <Smartphone className="ml-2" />
        </Button>
      </a>

      <a 
        href="https://www.icloud.com/shortcuts/e15b5336eba049e6a220f23e0900005e"
        target="_blank"
        rel="noopener noreferrer"
        className="w-full flex justify-center"
      >
        <Button 
          className="bg-black hover:bg-gray-800 text-white border-none w-full md:w-auto md:min-w-[240px] h-11"
        >
          {t('youtubeDT')} <Smartphone className="ml-2" />
        </Button>
      </a>
    </div>
  );
};