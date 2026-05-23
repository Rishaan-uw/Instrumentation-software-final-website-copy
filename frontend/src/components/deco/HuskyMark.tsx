interface Props {
  className?: string;
  title?: string;
}

/**
 * Husky Robotics mark - a stylised husky face built from triangular planes.
 * Drawn as an inline SVG so the icon has true transparency (no white box)
 * and inherits `currentColor`, which lets it blend with whatever background
 * its parent sits on. Mirrors the angular husky icon used in the team's
 * public site header.
 */
export default function HuskyMark({
  className,
  title = "Husky Robotics",
}: Props) {
  return (
    <svg
      viewBox="0 0 64 64"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      role="img"
      aria-label={title}
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinejoin="round"
      strokeLinecap="round"
    >
      <title>{title}</title>

      {/* Outer head silhouette - angular planes around a husky's face. */}
      <path
        d="
          M 32 6
          L 22 12
          L 12 8
          L 14 22
          L 8  30
          L 14 38
          L 18 50
          L 28 56
          L 32 60
          L 36 56
          L 46 50
          L 50 38
          L 56 30
          L 50 22
          L 52 8
          L 42 12
          Z"
      />

      {/* Forehead crease - the husky's signature mask split. */}
      <path d="M 32 14 L 28 26 L 32 32 L 36 26 Z" fill="currentColor" />

      {/* Inner ear shadows. */}
      <path d="M 18 13 L 22 22 L 16 20 Z" fill="currentColor" />
      <path d="M 46 13 L 42 22 L 48 20 Z" fill="currentColor" />

      {/* Eyes - sharp wedges. */}
      <path d="M 20 30 L 26 28 L 24 33 Z" fill="currentColor" />
      <path d="M 44 30 L 38 28 L 40 33 Z" fill="currentColor" />

      {/* Snout taper + nose. */}
      <path d="M 26 40 L 32 38 L 38 40 L 36 46 L 32 48 L 28 46 Z" />
      <path d="M 30 41 L 34 41 L 33 44 L 31 44 Z" fill="currentColor" />

      {/* Mouth split. */}
      <path d="M 32 48 L 32 54" />
    </svg>
  );
}
