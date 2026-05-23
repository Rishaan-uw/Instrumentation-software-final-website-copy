/**
 * Four L-bracket corner reticles drawn as absolutely-positioned borders.
 * Sits on top of any positioned parent to give it a viewfinder frame.
 */
export default function Reticle() {
  return (
    <>
      <span className="reticle-corner tl" />
      <span className="reticle-corner tr" />
      <span className="reticle-corner bl" />
      <span className="reticle-corner br" />
    </>
  );
}
