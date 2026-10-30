import { ROUTE } from '../../components/map/geo';
import { STOPS } from '../../config/places';

// the drawn route follows the rail corridors, so its length is a fair travel distance
const KM = Math.round(ROUTE.length / 10) * 10;

interface RouteCardProps {
  t: number;
  appear: number;
  reached: string[];
  current: string | null;
  completed?: string[];
  title?: string;
}

/** The journey at a glance: six stops from London to Edinburgh. */
export function RouteCard({ appear, reached, current, completed = [], title = 'London to Edinburgh' }: RouteCardProps) {
  return (
    <aside className="route-card" style={{ opacity: appear, transform: `translateX(${(1 - appear) * -16}px)` }} aria-label="The route">
      <p className="route-card__kicker">Coco's first journey</p>
      <h2 className="route-card__title">{title}</h2>
      <ol className="route-card__stops">
        {STOPS.map((s, i) => {
          const done = completed.includes(s.id);
          const on = reached.includes(s.id) || done;
          return (
            <li key={s.id} className={`${on ? 'is-on' : ''}${current === s.id ? ' is-current' : ''}${done ? ' is-done' : ''}`}>
              <span className="route-card__dot">{done ? '✓' : i + 1}</span>
              <span className="route-card__name">{s.name}</span>
              <span className="route-card__country">{s.country}</span>
            </li>
          );
        })}
      </ol>
      <p className="route-card__foot">
        {STOPS.length} stops · about {KM} km · {Math.round(KM * 0.621 / 10) * 10} miles
      </p>
    </aside>
  );
}
