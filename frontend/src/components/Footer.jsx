import logo from "../assets/logo.jpg";
import qr from "../assets/qrcode.jpg"; // Nahraj obrázek QR kódu jako PNG

export default function Footer() {
  return (
    <footer className="bg-black text-white py-10 px-4 text-center">
      <div className="flex flex-col md:flex-row items-center justify-between max-w-5xl mx-auto gap-6">
        <div className="space-y-2 text-left">
          <p>📧 naramkovamoda@email.cz</p>
          <p>📞 +420 776 47 97 47</p>
        
        </div>
        <img src={logo} alt="Logo" className="w-24" />

      </div>
      <p className="mt-6 text-sm text-gray-400">NÁRAMKOVÁ MÓDA – Ozdobte se jedinečností</p>
    </footer>
  );
}
