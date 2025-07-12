export default function Footer() {
  return (
    <footer className="bg-black text-white px-4 py-4">
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4 md:gap-0 text-center md:text-left">
        <div className="space-y-1">
          <p>📧 naramkovamoda@email.cz</p>
          <p>📞 +420 776 47 97 47</p>
        </div>
        <p className="text-sm text-gray-400 mt-2 md:mt-0">
          NÁRAMKOVÁ MÓDA – Ozdobte se jedinečností
        </p>
      </div>
    </footer>
  );
}
