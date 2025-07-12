import qrCode from "../assets/qr_code_fb.jpg";

export default function Footer() {
  return (
    <footer className="bg-black text-white py-6 px-4 text-center">
      <div className="flex flex-col md:flex-row items-center justify-between max-w-6xl mx-auto gap-6 text-sm md:text-base">
        {/* Kontakt vlevo */}
        <div className="space-y-1 text-left">
          <p>
            📧 <span className="font-semibold text-pink-500">naramkovamoda@email.cz</span>
          </p>
          <p>
            📞 <span className="font-semibold text-pink-500">+420 776 47 97 47</span>
          </p>
        </div>

        {/* Slogan uprostřed */}
        <div className="font-semibold text-pink-300 text-sm sm:text-base tracking-wide text-center">
          NÁRAMKOVÁ MÓDA – Ozdobte se jedinečností
        </div>

        {/* QR kód vpravo */}
        <div className="text-center">
          <p className="text-gray-300 mb-1">Sledujte nás na Facebooku:</p>
          <a
            href="https://www.facebook.com/groups/1051242036130223/?_rdr"
            target="_blank"
            rel="noopener noreferrer"
          >
            <img
              src={qrCode}
              alt="QR kód Facebook"
              className="h-20 w-20 sm:h-24 sm:w-24 mx-auto rounded shadow-md hover:scale-105 transition-transform duration-300"
            />
          </a>
        </div>
      </div>
    </footer>
  );
}
