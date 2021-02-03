
def make_zones_v2(planta, shafts, core, entrances, cat_area, areas, crystal_facs):
    zones = {}
    p_minx, p_miny, p_maxx, p_maxy = planta.bounds
    c_minx, c_miny, c_maxx, c_maxy = core.bounds
    factor = 0.1

    #cat_area = {1:80 ,2:230, 3:70, 4:70, 5:30, 6: 50, 7:20}
    #cat_area = {2:200, 3:40, 4:70, 5:30, 6: 50, 7:20}
    #cat_area = {4:70}
    #cat_area = {2: 68.75, 4: 30.6116}
    cat_area = {1: 68.75, 2: 230, 3: 58.36, 4: 30.6116, 5: 16.790499999999998}
    core_bounds = [core.bounds]
    entrances_bounds = list(map(lambda x: x.buffer(1.5, cap_style=3).bounds, entrances))
    crystal_facs_bounds = list(map(lambda x: x.bounds, crystal_facs))
    areas_bounds = []
    for key, area in areas.items():
        areas_bounds.append(area.bounds)

    elements_idx = rtree.index.Index()

    crystal_adj_qty = {}
    entrances_adj_qty = {}
    shafts_adj_qty = {}
    core_adj_qty = {}

    if len(shafts) > 0:
        has_shaft = True
    else:
        has_shaft = False

    if has_shaft:
        shafts_bounds = list(map(lambda x: x.bounds, shafts))
        elements = core_bounds + shafts_bounds + entrances_bounds + crystal_facs_bounds + areas_bounds
        for i, e in enumerate(elements):
            elements_idx.insert(i, e)

        for key, area in areas.items():
            crystal_adj = [obj for obj in list(elements_idx.nearest(area.bounds, objects=True)) if tuple(obj.bbox) in crystal_facs_bounds]
            shafts_adj = [obj for obj in list(elements_idx.nearest(area.bounds, objects=True)) if tuple(obj.bbox) in shafts_bounds]
            entrances_adj = [obj for obj in list(elements_idx.nearest(area.bounds, objects=True)) if tuple(obj.bbox) in entrances_bounds]
            core_adj = [obj for obj in list(elements_idx.nearest(area.bounds, objects=True)) if tuple(obj.bbox) in core_bounds]
            crystal_adj_qty[key] = len(crystal_adj)
            shafts_adj_qty[key] = len(shafts_adj)
            entrances_adj_qty[key] = len(entrances_adj)
            core_adj_qty[key] = len(core_adj)
    else:
        elements = core_bounds + entrances_bounds + crystal_facs_bounds + areas_bounds
        for i, e in enumerate(elements):
            elements_idx.insert(i, e)

        for key, area in areas.items():
            crystal_adj = [obj for obj in list(elements_idx.nearest(area.bounds, objects=True)) if tuple(obj.bbox) in crystal_facs_bounds]
            entrances_adj = [obj for obj in list(elements_idx.nearest(area.bounds, objects=True)) if tuple(obj.bbox) in entrances_bounds]
            core_adj = [obj for obj in list(elements_idx.nearest(area.bounds, objects=True)) if tuple(obj.bbox) in core_bounds]
            crystal_adj_qty[key] = len(crystal_adj)
            entrances_adj_qty[key] = len(entrances_adj)
            core_adj_qty[key] = len(core_adj)
    print("adyacentes a cristal:", crystal_adj_qty)
    print("adyacentes al core:", core_adj_qty)
    # Zona de servicios
    # Se selecciona solo 1 area que tenga mas shafts cercanos
    sv_selected_zone = None
    sv_nearest = None
    sv_nearest_idx = None
    if 4 in cat_area:
        if has_shaft:
            sv_candidate_idx = max(shafts_adj_qty, key=shafts_adj_qty.get)
        else:
            sv_candidate_idx = [k for k, v in core_adj_qty.items() if v == max(core_adj_qty.values())]
            sv_candidate_idx = [k for k, v in crystal_adj_qty.items() if v >= min(crystal_adj_qty.values()) and v < max(crystal_adj_qty.values()) and k in sv_candidate_idx]
            sv_candidate_zones = {}
            for c in sv_candidate_idx:
                sv_candidate_zones[c] = areas[c]
            sv_candidate_zones_areas = {k: v.area for k, v in sv_candidate_zones.items()}
            sv_candidate_idx = max(sv_candidate_zones_areas, key=sv_candidate_zones_areas.get)
        print("Candidato zona de servicios:", sv_candidate_idx)
        
        sv_selected_zone = areas[sv_candidate_idx]
        zones['ZONA SERVICIOS'] = sv_selected_zone
        areas.pop(sv_candidate_idx, None)
        shafts_adj_qty.pop(sv_candidate_idx, None)
        crystal_adj_qty.pop(sv_candidate_idx, None)
        entrances_adj_qty.pop(sv_candidate_idx, None)
        sv_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(sv_selected_zone.bounds, objects=True))))
        sv_nearest_idx = [k for k,v in areas.items() if v.bounds in sv_nearest]

    # Zonas de puestos de trabajo
    pt_selected_zones = None
    pt_nearest = None
    pt_nearest_idx = None
    if 2 in cat_area:
        if cat_area[2] > planta.area*0.3:
            n_pt_zones = 2
        else:
            n_pt_zones = 1

        pt_candidate_idx = []
        if sv_selected_zone:
            # Arreglo de indices de zonas cercanas al area de servicios
            pt_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values()) and v <= max(crystal_adj_qty.values()) and k in sv_nearest_idx]
        else:
            pt_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values()) and v <= max(crystal_adj_qty.values())]
        pt_candidate_zones = {}
        print("Candidatos puestos de trabajo:", pt_candidate_idx)
        # Se asume que hay al menos 1 zona con muchas fachadas de cristal cercanas
        for c in pt_candidate_idx:
            pt_candidate_zones[c] = areas[c]
        if len(pt_candidate_zones) < 2:
            # Si hay una zona con area maxima absoluta, se selecciona la primera zona siguiente que tenga area maxima
            pt_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values()) and v <= max(crystal_adj_qty.values()) and not k in pt_candidate_idx]
            pt_candidate_zones[pt_candidate_idx[0]] = areas[pt_candidate_idx[0]]
        # Se seleccionan solo 2 zonas de la lista de candidatas
        pt_selected_zones = []
        pt_nearest_idx = []
        for i in range(n_pt_zones):
            pt_candidate_zones_areas = {k: v.area for k, v in pt_candidate_zones.items()}
            selected_zone_idx = max(pt_candidate_zones_areas, key=pt_candidate_zones_areas.get)
            selected_zone = pt_candidate_zones[selected_zone_idx]
            pt_selected_zones.append(selected_zone)
            del pt_candidate_zones[selected_zone_idx]
            del pt_candidate_zones_areas[selected_zone_idx]
            areas.pop(selected_zone_idx, None)
            shafts_adj_qty.pop(selected_zone_idx, None)
            crystal_adj_qty.pop(selected_zone_idx, None)
            entrances_adj_qty.pop(selected_zone_idx, None)
            pt_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(selected_zone.bounds, objects=True))))
            for k,v in areas.items():
                if v.bounds in pt_nearest and not k in pt_nearest_idx:
                    pt_nearest_idx.append(k)
            zones['ZONA PUESTOS DE TRABAJO ' + str(i)] = selected_zone
    
    # Zona de soporte
    sp_selected_zone = None
    sp_nearest = None
    sp_nearest_idx = None
    if 5 in cat_area:
        sp_candidate_idx = [k for k, v in entrances_adj_qty.items() if v == max(entrances_adj_qty.values())]
        if not sp_candidate_idx:
            sp_candidate_idx = [k for k, v in core_adj_qty.items() if v == max(core_adj_qty.values())]

        print("Candidatos zona soporte:", sp_candidate_idx)
        # Se asume que hay al menos 1 zona candidata
        if len(sp_candidate_idx) > 1:
            sp_candidate_zones = {}
            for c in sp_candidate_idx:
                sp_candidate_zones[c] = areas[c]
            # Si hay mas de 1 zona cercana a alguna entrada, se selecciona la que tenga menor area
            sp_candidate_zones_areas = {k: v.area for k, v in sp_candidate_zones.items()}
            sp_selected_zone_idx = max(sp_candidate_zones_areas, key=sp_candidate_zones_areas.get)
            sp_selected_zone = sp_candidate_zones[sp_selected_zone_idx]
        elif len(sp_candidate_idx) == 1:
            sp_selected_zone_idx = sp_candidate_idx[0]
            sp_selected_zone = areas[sp_selected_zone_idx]
        else:
            pass

        areas.pop(sp_selected_zone_idx, None)
        shafts_adj_qty.pop(sp_selected_zone_idx, None)
        crystal_adj_qty.pop(sp_selected_zone_idx, None)
        entrances_adj_qty.pop(sp_selected_zone_idx, None)
        zones['ZONA SOPORTE'] = sp_selected_zone
        sp_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(sp_selected_zone.bounds, objects=True))))
        sp_nearest_idx = [k for k,v in areas.items() if v.bounds in sp_nearest]

    # Zona de puestos de trabajo privado
    ptp_selected_zone = None
    ptp_nearest = None
    ptp_nearest_idx = None
    if 3 in cat_area:
        # Indices de areas cercanas a zona de soporte
        if sp_selected_zone and sv_selected_zone:
            # Se buscan candidatos que tengan fachadas de cristal adyacentes y que no esten cerca de la zona de soporte
            ptp_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values()) and v < max(crystal_adj_qty.values()) and (not k in sp_nearest_idx and not k in sv_nearest_idx)]

            if not ptp_candidate_idx:
                # En caso que NO se haya encontrado a lo menos un candidato que cumpla con el criterio, se relaja la restriccion
                ptp_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values()) and v < max(crystal_adj_qty.values()) and (not k in sp_nearest_idx or not k in sv_nearest_idx)]
                if not ptp_candidate_idx:
                    ptp_candidate_idx = [k for k, v in crystal_adj_qty.items() if not k in sp_nearest_idx]
                    if not ptp_candidate_idx:
                        ptp_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values()) and v < max(crystal_adj_qty.values())]
        elif sp_selected_zone:
            # Se buscan candidatos que tengan fachadas de cristal adyacentes y que no esten cerca de la zona de soporte
            ptp_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values()) and v < max(crystal_adj_qty.values()) and not k in sp_nearest_idx]
            if not ptp_candidate_idx:
                ptp_candidate_idx = [k for k, v in crystal_adj_qty.items() if not k in sp_nearest_idx]
                if not ptp_candidate_idx:
                    ptp_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values()) and v < max(crystal_adj_qty.values())]
        elif sv_selected_zone:
             # Se buscan candidatos que tengan fachadas de cristal adyacentes y que no esten cerca de la zona de soporte
            ptp_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values()) and v < max(crystal_adj_qty.values()) and not k in sv_nearest_idx]
            if not ptp_candidate_idx:
                ptp_candidate_idx = [k for k, v in crystal_adj_qty.items() if not k in sv_nearest_idx]
                if not ptp_candidate_idx:
                    ptp_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values()) and v < max(crystal_adj_qty.values())]
        else:
            ptp_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values()) and v < max(crystal_adj_qty.values())]
            if not ptp_candidate_idx:
                ptp_candidate_idx = [k for k, v in crystal_adj_qty.items() if v >= min(crystal_adj_qty.values())]
        
        print("Candidatos puestos de trabajo privado:")
        print(ptp_candidate_idx)

        # En caso que se haya encontrado mas de un candidato que cumpla con algun criterio, se elige el que tenga mas fachadas de cristal
        if len(ptp_candidate_idx) > 1:
            ptp_candidate_zones = {}
            for c in ptp_candidate_idx:
                ptp_candidate_zones[c] = areas[c]
            ptp_candidate_zones_areas = {k: v.area for k, v in ptp_candidate_zones.items() if crystal_adj_qty[k] > min(crystal_adj_qty.values())}
            ptp_selected_zone_idx = max(ptp_candidate_zones_areas, key=ptp_candidate_zones_areas.get)
            ptp_selected_zone = ptp_candidate_zones[ptp_selected_zone_idx]
        elif len(ptp_candidate_idx) == 1:
            ptp_selected_zone_idx = ptp_candidate_idx[0]
            ptp_selected_zone = areas[ptp_selected_zone_idx]
        else:
            pass

        areas.pop(ptp_selected_zone_idx, None)
        shafts_adj_qty.pop(ptp_selected_zone_idx, None)
        crystal_adj_qty.pop(ptp_selected_zone_idx, None)
        entrances_adj_qty.pop(ptp_selected_zone_idx, None)
        zones['ZONA TRABAJO PRIVADO'] = ptp_selected_zone
        ptp_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(ptp_selected_zone.bounds, objects=True))))
        ptp_nearest_idx = [k for k,v in areas.items() if v.bounds in ptp_nearest]

    # Zona reuniones formales
    if 1 in cat_area:
        if ptp_selected_zone:
            # Se buscan indices de areas disponibles cercanas a la zona seleccionada como trabajo privado
            if sp_nearest_idx and sv_nearest_idx:
                rf_candidate_idx = [k for k, v in areas.items() if (not k in sp_nearest_idx and not k in sv_nearest_idx) and k in ptp_nearest_idx]
                if not rf_candidate_idx:
                    rf_candidate_idx = [k for k, v in areas.items() if (not k in sp_nearest_idx or not k in sv_nearest_idx) and k in ptp_nearest_idx]
                    if not rf_candidate_idx:
                        rf_candidate_idx = [k for k, v in areas.items() if k in ptp_nearest_idx]
            elif sp_nearest_idx:
                rf_candidate_idx = [k for k, v in areas.items() if not k in sp_nearest_idx and k in ptp_nearest_idx]
                if not rf_candidate_idx:
                    rf_candidate_idx = [k for k, v in areas.items() if k in ptp_nearest_idx]
            elif sv_nearest_idx:
                rf_candidate_idx = [k for k, v in areas.items() if not k in sv_nearest_idx and k in ptp_nearest_idx]
                if not rf_candidate_idx:
                    rf_candidate_idx = [k for k, v in areas.items() if k in ptp_nearest_idx]
            else:
                rf_candidate_idx = [k for k, v in areas.items() if k in ptp_nearest_idx]
        else:
            if sp_nearest_idx and sv_nearest_idx:
                rf_candidate_idx = [k for k, v in areas.items() if (not k in sp_nearest_idx and not k in sv_nearest_idx)] 
                if not rf_candidate_idx:
                    rf_candidate_idx = [k for k, v in areas.items() if (not k in sp_nearest_idx or not k in sv_nearest_idx)]
                    if not rf_candidate_idx:
                        rf_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values()) and v <= max(crystal_adj_qty.values())]
            elif sp_nearest_idx:
                rf_candidate_idx = [k for k, v in areas.items() if not k in sp_nearest_idx]
                if not rf_candidate_idx:
                    rf_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values()) and v <= max(crystal_adj_qty.values())]
            elif sv_nearest_idx:
                rf_candidate_idx = [k for k, v in areas.items() if not k in sv_nearest_idx]
                if not rf_candidate_idx:
                    rf_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values()) and v <= max(crystal_adj_qty.values())]
            else:
                rf_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values()) and v <= max(crystal_adj_qty.values())]

        print("Candidatos reuniones formales:")
        print(rf_candidate_idx)
        rf_candidate_zones = {}
        # En caso que se haya encontrado mas de un candidato que cumpla con algun criterio, se elige el de mayor area
        if len(rf_candidate_idx) > 1:
            for c in rf_candidate_idx:
                rf_candidate_zones[c] = areas[c]
            rf_candidate_zones_areas = {k: v.area for k, v in rf_candidate_zones.items()}
            rf_selected_zone_idx = max(rf_candidate_zones_areas, key=rf_candidate_zones_areas.get)
            rf_selected_zone = rf_candidate_zones[rf_selected_zone_idx]
        elif len(rf_candidate_idx) == 1:
            rf_selected_zone_idx = rf_candidate_idx[0]
            rf_selected_zone = areas[rf_selected_zone_idx]
        else:
            pass

        areas.pop(rf_selected_zone_idx, None)
        shafts_adj_qty.pop(rf_selected_zone_idx, None)
        crystal_adj_qty.pop(rf_selected_zone_idx, None)
        entrances_adj_qty.pop(rf_selected_zone_idx, None)
        zones['ZONA SALAS REUNION FORMAL'] = rf_selected_zone

     # Zona reuniones informales (o puestos de trabajo informal)
    ri_selected_zone = None
    if 6 in cat_area:
        # Se buscan como candidatos, indices de areas disponibles cercanas a la zonas seleccionadas como puestos de trabajo
        if pt_nearest_idx:
            ri_candidate_idx = [k for k,v in areas.items() if k in pt_nearest_idx]
            rf_candidate_idx_filter = [k for k, v in crystal_adj_qty.items() if v == min(crystal_adj_qty.values())]
            if rf_candidate_idx_filter:
                ri_candidate_idx = rf_candidate_idx_filter
            if not ri_candidate_idx:
                ri_candidate_idx = [k for k,v in areas.items()]
        else:
            ri_candidate_idx = [k for k,v in areas.items()]
        print("Candidatos reuniones informales:", ri_candidate_idx)

        # En caso que se haya encontrado mas de un candidato que cumpla con algun criterio, se elige el de mayor area
        if len(ri_candidate_idx) > 1:
            ri_candidate_zones = {}
            for c in ri_candidate_idx:
                ri_candidate_zones[c] = areas[c]
            ri_candidate_zones_areas = {k: v.area for k, v in ri_candidate_zones.items()}
            ri_selected_zone_idx = max(ri_candidate_zones_areas, key=ri_candidate_zones_areas.get)
            ri_selected_zone = ri_candidate_zones[ri_selected_zone_idx]
        elif len(ri_candidate_idx) == 1:
            ri_selected_zone_idx = ri_candidate_idx[0]
            ri_selected_zone = areas[ri_selected_zone_idx]
        else:
            pass
        
        areas.pop(ri_selected_zone_idx, None)
        shafts_adj_qty.pop(ri_selected_zone_idx, None)
        crystal_adj_qty.pop(ri_selected_zone_idx, None)
        entrances_adj_qty.pop(ri_selected_zone_idx, None)
        zones['ZONA REUNIONES INFORMALES'] = ri_selected_zone

    # Zona especiales
    esp_selected_zone = None
    if 7 in cat_area:
        if sp_nearest_idx:
            esp_candidate_idx = [k for k,v in areas.items() if k in sp_nearest_idx]
            if not esp_candidate_idx:
                esp_candidate_idx = [k for k,v in areas.items()]
        else:
            esp_candidate_idx = [k for k, v in entrances_adj_qty.items() if v == max(entrances_adj_qty.values())]
            if not esp_candidate_idx:
                esp_candidate_idx = [k for k,v in areas.items()]

        print("Candidatos especiales:", esp_candidate_idx)
        if len(esp_candidate_idx) > 1:
            esp_candidate_zones = {}
            for c in esp_candidate_idx:
                esp_candidate_zones[c] = areas[c]
            esp_candidate_zones_areas = {k: v.area for k, v in esp_candidate_zones.items()}
            esp_selected_zone_idx = max(esp_candidate_zones_areas, key=esp_candidate_zones_areas.get)
            esp_selected_zone = esp_candidate_zones[esp_selected_zone_idx]
        elif len(esp_candidate_idx) == 1:
            esp_selected_zone_idx = esp_candidate_idx[0]
            esp_selected_zone = areas[esp_selected_zone_idx]
        else:
            pass
        
        areas.pop(esp_selected_zone_idx, None)
        shafts_adj_qty.pop(esp_selected_zone_idx, None)
        crystal_adj_qty.pop(esp_selected_zone_idx, None)
        entrances_adj_qty.pop(esp_selected_zone_idx, None)
            
        zones['ZONA ESPECIALES'] = esp_selected_zone

    last_areas_len = len(areas)
    while len(areas) > 0:
        if sv_selected_zone and sv_selected_zone.area < cat_area[4] + factor*cat_area[4]:
            # Expasión zona de servicios
            sv_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(sv_selected_zone.bounds, objects=True))))
            sv_nearest_idx = [k for k,v in areas.items() if v.bounds in sv_nearest]
            nearest_len = {idx: sv_selected_zone.intersection(areas[idx]).length for idx in sv_nearest_idx if sv_selected_zone.intersection(areas[idx]).geom_type == 'LineString' or sv_selected_zone.intersection(areas[idx]).geom_type == 'MultiLineString'}
            print("hola5:", nearest_len)
            if nearest_len:
                nearest_candidate_idx = max(nearest_len, key=nearest_len.get)
                sv_candidate_zone = unary_union([sv_selected_zone, areas[nearest_candidate_idx]])
                if sv_candidate_zone.geom_type == 'Polygon':
                    sv_selected_zone = sv_candidate_zone
                    areas.pop(nearest_candidate_idx, None)
                    shafts_adj_qty.pop(nearest_candidate_idx, None)
                    crystal_adj_qty.pop(nearest_candidate_idx, None)
                    entrances_adj_qty.pop(nearest_candidate_idx, None)
                    zones['ZONA SERVICIOS'] = sv_selected_zone
                    sv_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(sv_selected_zone.bounds, objects=True))))
                    sv_nearest_idx = [k for k,v in areas.items() if v.bounds in sv_nearest]
            elif len(areas) < 1:
                break
        if pt_selected_zones:
            # Expasión zonas de puestos de trabajo
            print("hola")
            print(len(areas))
            for i in range(n_pt_zones):
                pt_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(pt_selected_zones[i].bounds, objects=True))))
                pt_nearest_idx = [k for k,v in areas.items() if v.bounds in pt_nearest]
                pt_nearest_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values()) and k in pt_nearest_idx]
                print("hola6:", pt_nearest_idx)
                nearest_len = {idx: pt_selected_zones[i].intersection(areas[idx]).length for idx in pt_nearest_idx}
                print("hola7:", nearest_len)
                if nearest_len:
                    print("hola8:", nearest_len)
                    nearest_candidate_idx = max(nearest_len, key=nearest_len.get)
                    pt_candidate_zone = unary_union([pt_selected_zones[i], areas[nearest_candidate_idx]])
                    if pt_candidate_zone.geom_type == 'Polygon':
                        pt_selected_zones[i] = pt_candidate_zone
                        zones['ZONA PUESTOS DE TRABAJO ' + str(i)] = pt_selected_zones[i]
                        areas.pop(nearest_candidate_idx, None)
                        shafts_adj_qty.pop(nearest_candidate_idx, None)
                        crystal_adj_qty.pop(nearest_candidate_idx, None)
                        entrances_adj_qty.pop(nearest_candidate_idx, None)
                elif len(areas) < 1:
                    break

        if sp_selected_zone and sp_selected_zone.area < cat_area[5] + factor*cat_area[5]:
            sp_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(sp_selected_zone.bounds, objects=True))))
            sp_nearest_idx = [k for k,v in areas.items() if v.bounds in sp_nearest]
            sp_nearest_idx_filter = [k for k, v in crystal_adj_qty.items() if v == min(crystal_adj_qty.values()) and k in sp_nearest_idx]
            if sp_nearest_idx_filter:
                sp_nearest_idx = sp_nearest_idx_filter
            nearest_len = {idx: sp_selected_zone.intersection(areas[idx]).length for idx in sp_nearest_idx if sp_selected_zone.intersection(areas[idx]).geom_type == 'LineString' or sp_selected_zone.intersection(areas[idx]).geom_type == 'MultiLineString'}
            print("hola10:", nearest_len)
            if nearest_len:
                nearest_candidate_idx = max(nearest_len, key=nearest_len.get)
                sp_candidate_zone = unary_union([sp_selected_zone, areas[nearest_candidate_idx]])
                if sp_candidate_zone.geom_type == 'Polygon':
                    sp_selected_zone = sp_candidate_zone
                    areas.pop(nearest_candidate_idx, None)
                    shafts_adj_qty.pop(nearest_candidate_idx, None)
                    crystal_adj_qty.pop(nearest_candidate_idx, None)
                    entrances_adj_qty.pop(nearest_candidate_idx, None)
                    zones['ZONA SOPORTE'] = sp_selected_zone
            elif len(areas) < 1:
                break

        if ptp_selected_zone and ptp_selected_zone.area < cat_area[3] + factor*cat_area[3]:
            ptp_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(ptp_selected_zone.bounds, objects=True))))
            ptp_nearest_idx = [k for k,v in areas.items() if v.bounds in ptp_nearest]
            ptp_nearest_idx_filter = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values()) and k in ptp_nearest_idx]
            if ptp_nearest_idx_filter:
                ptp_nearest_idx = ptp_nearest_idx_filter
            nearest_len = {idx: ptp_selected_zone.intersection(areas[idx]).length for idx in ptp_nearest_idx if ptp_selected_zone.intersection(areas[idx]).geom_type == 'LineString' or ptp_selected_zone.intersection(areas[idx]).geom_type == 'MultiLineString'}
            if nearest_len:
                nearest_candidate_idx = max(nearest_len, key=nearest_len.get)
                ptp_candidate_zone = unary_union([ptp_selected_zone, areas[nearest_candidate_idx]])
                if ptp_candidate_zone.geom_type == 'Polygon':
                    ptp_selected_zone = ptp_candidate_zone
                    areas.pop(nearest_candidate_idx, None)
                    shafts_adj_qty.pop(nearest_candidate_idx, None)
                    crystal_adj_qty.pop(nearest_candidate_idx, None)
                    entrances_adj_qty.pop(nearest_candidate_idx, None)
                    zones['ZONA TRABAJO PRIVADO'] = ptp_selected_zone
            elif len(areas) < 1:
                break
        
        if rf_selected_zone:
            rf_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(rf_selected_zone.bounds, objects=True))))
            rf_nearest_idx = [k for k,v in areas.items() if v.bounds in rf_nearest]
            rf_nearest_idx_filter = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values()) and k in rf_nearest_idx]
            if rf_nearest_idx_filter:
                rf_nearest_idx = rf_nearest_idx_filter
            nearest_len = {idx: rf_selected_zone.intersection(areas[idx]).length for idx in rf_nearest_idx if rf_selected_zone.intersection(areas[idx]).geom_type == 'LineString' or rf_selected_zone.intersection(areas[idx]).geom_type == 'MultiLineString'}
            if nearest_len:
                nearest_candidate_idx = max(nearest_len, key=nearest_len.get)
                rf_candidate_zone = unary_union([rf_selected_zone, areas[nearest_candidate_idx]])
                if rf_candidate_zone.geom_type == 'Polygon':
                    rf_selected_zone = rf_candidate_zone
                    areas.pop(nearest_candidate_idx, None)
                    shafts_adj_qty.pop(nearest_candidate_idx, None)
                    crystal_adj_qty.pop(nearest_candidate_idx, None)
                    entrances_adj_qty.pop(nearest_candidate_idx, None)
                    zones['ZONA SALAS REUNION FORMAL'] = rf_selected_zone
            elif len(areas) < 1:
                break

        if ri_selected_zone and ri_selected_zone.area < cat_area[6] + factor*cat_area[6]:
            ri_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(ri_selected_zone.bounds, objects=True))))
            ri_nearest_idx = [k for k,v in areas.items() if v.bounds in ri_nearest]
            nearest_len = {idx: ri_selected_zone.intersection(areas[idx]).length for idx in ri_nearest_idx if ri_selected_zone.intersection(areas[idx]).geom_type == 'LineString' or ri_selected_zone.intersection(areas[idx]).geom_type == 'MultiLineString'}
            if nearest_len:
                nearest_candidate_idx = max(nearest_len, key=nearest_len.get)
                ri_candidate_zone = unary_union([ri_selected_zone, areas[nearest_candidate_idx]])
                if ri_candidate_zone.geom_type == 'Polygon':
                    ri_selected_zone = ri_candidate_zone
                    areas.pop(nearest_candidate_idx, None)
                    shafts_adj_qty.pop(nearest_candidate_idx, None)
                    crystal_adj_qty.pop(nearest_candidate_idx, None)
                    entrances_adj_qty.pop(nearest_candidate_idx, None)
                    zones['ZONA REUNIONES INFORMALES'] = ri_selected_zone
            elif len(areas) < 1:
                break

        if esp_selected_zone and esp_selected_zone.area < cat_area[7] + factor*cat_area[7]:
            esp_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(esp_selected_zone.bounds, objects=True))))
            esp_nearest_idx = [k for k,v in areas.items() if v.bounds in esp_nearest]
            esp_nearest_idx_filter = [k for k, v in crystal_adj_qty.items() if v == min(crystal_adj_qty.values()) and k in esp_nearest_idx]
            if esp_nearest_idx_filter:
                esp_nearest_idx = esp_nearest_idx_filter
            nearest_len = {idx: esp_selected_zone.intersection(areas[idx]).length for idx in esp_nearest_idx if esp_selected_zone.intersection(areas[idx]).geom_type == 'LineString' or esp_selected_zone.intersection(areas[idx]).geom_type == 'MultiLineString'}
            if nearest_len:
                nearest_candidate_idx = max(nearest_len, key=nearest_len.get)
                esp_candidate_zone = unary_union([esp_selected_zone, areas[nearest_candidate_idx]])
                if esp_selected_zone.geom_type == 'Polygon':
                    esp_selected_zone = esp_candidate_zone
                    areas.pop(nearest_candidate_idx, None)
                    shafts_adj_qty.pop(nearest_candidate_idx, None)
                    crystal_adj_qty.pop(nearest_candidate_idx, None)
                    entrances_adj_qty.pop(nearest_candidate_idx, None)
                    zones['ZONA ESPECIALES'] = esp_selected_zone
            elif len(areas) < 1:
                break
        if last_areas_len == len(areas):
            break
        else:
            last_areas_len = len(areas)
    return zones