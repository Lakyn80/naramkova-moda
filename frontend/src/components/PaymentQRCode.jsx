import { useEffect, useRef, useState } from "react";
import QRCode from "qrcode";
import { buildSpdPayload } from "../utils/spd";

export default function PaymentQRCode({ iban, amount, vs, msg, size = 256 }) {
  const canvasRef = useRef(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const draw = async () => {
      setError("");
      try {
        if (!iban || !amount || Number(amount) <= 0) {
          setError("Chybí IBAN nebo částka.");
          return;
        }
        const payload = buildSpdPayload({ iban, amount, vs, msg });
        await QRCode.toCanvas(canvasRef.current, payload, { width: size, margin: 1 });
      } catch (e) {
        setError(String(e?.message || e));
      }
    };
    draw();
  }, [iban, amount, vs, msg, size]);

  if (error) return <div className="text-red-600">{error}</div>;

  return (
    <div className="flex flex-col items-center gap-2">
      <canvas ref={canvasRef} className="border rounded-lg shadow" />
      <div className="text-sm text-gray-600 text-center">
        Částka: <strong>{Number(amount).toFixed(2)} CZK</strong>
        {vs ? <> · VS: <strong>{vs}</strong></> : null}
        {msg ? <> · Zpráva: <strong>{msg}</strong></> : null}
      </div>
    </div>
  );
}
