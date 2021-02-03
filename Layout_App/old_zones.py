'''
        # Zona de servicios
        sv_candidate_idx = max(shafts_adj_qty, key=shafts_adj_qty.get)
        sv_selected_zone = areas[sv_candidate_idx]
        areas.pop(sv_candidate_idx, None)
        shafts_adj_qty.pop(sv_candidate_idx, None)
        crystal_adj_qty.pop(sv_candidate_idx, None)
        entrances_adj_qty.pop(sv_candidate_idx, None)
        # Arreglo de indices de zonas cercanas al area de servicios
        sv_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(sv_selected_zone.bounds, objects=True))))
        sv_nearest_idx = [k for k,v in areas.items() if v.bounds in sv_nearest]
        print("indices cercanos a area de servicios: ", sv_nearest_idx)

        # Zonas de puestos de trabajo
        print("Fachadas de cristal adjacentes:")
        print(crystal_adj_qty)

        # Se seleccionan como candidatas las areas que tengan mayores cristales adyacentes y que ademas esten cerca del area de servicios
        pt_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values()) and v <= max(crystal_adj_qty.values()) and (shafts_adj_qty[k] > 0 or k in sv_nearest_idx)]
        print("Candidatos puestos de trabajo:", pt_candidate_idx)
        if not pt_candidate_idx:
            pt_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values()) and v <= max(crystal_adj_qty.values())]
        pt_candidate_zones = {}
        # Se asume que hay al menos 1 zona con muchas fachadas de cristal cercanas
        for c in pt_candidate_idx:
            pt_candidate_zones[c] = areas[c]
        if len(pt_candidate_zones) < 2:
            # Si hay una zona con area maxima absoluta, se selecciona la primera zona siguiente que tenga area maxima
            pt_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values()) and v <= max(crystal_adj_qty.values()) and not k in pt_candidate_idx]
            pt_candidate_zones[pt_candidate_idx[0]] = areas[pt_candidate_idx[0]]
        # Se seleccionan solo 2 zonas de la lista de candidatas
        pt_selected_zones = []
        for i in range(2):
            pt_candidate_zones_areas = {k: v.area for k, v in pt_candidate_zones.items()}
            selected_zone_idx = max(pt_candidate_zones_areas, key=pt_candidate_zones_areas.get)
            selected_zone = pt_candidate_zones[selected_zone_idx]
            pt_selected_zones.append(selected_zone)
            zones.append([selected_zone, 'ZONA PUESTOS DE TRABAJO'])
            del pt_candidate_zones[selected_zone_idx]
            del pt_candidate_zones_areas[selected_zone_idx]
            areas.pop(selected_zone_idx, None)
            shafts_adj_qty.pop(selected_zone_idx, None)
            crystal_adj_qty.pop(selected_zone_idx, None)
            entrances_adj_qty.pop(selected_zone_idx, None)

        print("Fachadas de cristal adjacentes (despues de filtro):")
        print(crystal_adj_qty)
        print("max:", [k for k, v in crystal_adj_qty.items() if v == max(crystal_adj_qty.values())])
        print("Shaft adjacentes:")
        print(shafts_adj_qty)
        print("max:", [k for k, v in shafts_adj_qty.items() if v == max(shafts_adj_qty.values())])

        
        # Zona de soporte
        sp_candidate_idx = [k for k, v in entrances_adj_qty.items() if v == max(entrances_adj_qty.values())]
        print("Entradas adjacentes:")
        print(entrances_adj_qty)
        print("max:", sp_candidate_idx)

        # Se asume que hay al menos 1 zona cercana a alguna entrada
        if len(sp_candidate_idx) > 1:
            sp_candidate_zones = {}
            for c in sp_candidate_idx:
                sp_candidate_zones[c] = areas[c]
            # Si hay mas de 1 zona cercana a alguna entrada, se selecciona la que tenga menor area
            sp_candidate_zones_areas = {k: v.area for k, v in sp_candidate_zones.items()}
            sp_selected_zone_idx = min(sp_candidate_zones_areas, key=sp_candidate_zones_areas.get)
            sp_selected_zone = sp_candidate_zones[sp_selected_zone_idx]
        else:
            sp_selected_zone_idx = sp_candidate_idx[0]
            sp_selected_zone = areas[sp_selected_zone_idx]

        zones.append([sp_selected_zone, 'ZONA SOPORTE'])
        areas.pop(sp_selected_zone_idx, None)
        shafts_adj_qty.pop(sp_selected_zone_idx, None)
        crystal_adj_qty.pop(sp_selected_zone_idx, None)
        entrances_adj_qty.pop(sp_selected_zone_idx, None)
        
        # Indices de areas cercanas a zona de soporte
        sp_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(sp_selected_zone.bounds, objects=True))))
        sp_nearest_idx = [k for k,v in areas.items() if v.bounds in sp_nearest]
        print("indices cercanos a area de servicios: ", sp_nearest_idx)

        # Zona de puestos de trabajo privado
        # Se buscan candidatos que tengan fachadas de cristal adyacentes y que no esten cerca de la zona de soporte
        ptp_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values()) and v <= max(crystal_adj_qty.values()) and not k in sp_nearest_idx]
        print(crystal_adj_qty)
        print("Candidatos puestos de trabajo privado:")
        print(ptp_candidate_idx)

        if not ptp_candidate_idx:
            # En caso que NO se haya encontrado a lo menos un candidato que cumpla con el criterio, se relaja la restriccion
            ptp_candidate_idx = [k for k, v in crystal_adj_qty.items() if not k in sp_nearest_idx]

        # En caso que se haya encontrado mas de un candidato que cumpla con algun criterio, se elige el que tenga mas fachadas de cristal
        if len(ptp_candidate_idx) > 1:
            ptp_candidate_zones = {}
            for c in ptp_candidate_idx:
                ptp_candidate_zones[c] = areas[c]
            ptp_candidate_zones_areas = {k: crystal_adj_qty[k] for k, v in ptp_candidate_zones.items()}
            ptp_selected_zone_idx = max(ptp_candidate_zones_areas, key=ptp_candidate_zones_areas.get)
            ptp_selected_zone = ptp_candidate_zones[ptp_selected_zone_idx]
        else:
            ptp_selected_zone_idx = ptp_candidate_idx[0]
            ptp_selected_zone = areas[ptp_selected_zone_idx]

        zones.append([ptp_selected_zone, 'ZONA TRABAJO PRIVADO'])
        areas.pop(ptp_selected_zone_idx, None)
        shafts_adj_qty.pop(ptp_selected_zone_idx, None)
        crystal_adj_qty.pop(ptp_selected_zone_idx, None)
        entrances_adj_qty.pop(ptp_selected_zone_idx, None)

        # Zona reuniones formales
        # Se buscan indices de areas disponibles cercanas a la zona seleccionada como trabajo privado
        ptp_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(ptp_selected_zone.bounds, objects=True))))
        ptp_nearest_idx = [k for k,v in areas.items() if v.bounds in ptp_nearest]
        print("indices cercanos a trabajo privado: ", ptp_nearest_idx)

        
        rf_candidate_idx = [k for k, v in areas.items() if (not k in sp_nearest_idx and not k in sv_nearest_idx) and k in ptp_nearest_idx]
        print("Candidatos reuniones formales:")
        print(rf_candidate_idx)
        rf_candidate_zones = {}
        if not rf_candidate_idx:
            rf_candidate_idx = [k for k, v in areas.items() if (not k in sp_nearest_idx or not k in sv_nearest_idx) and k in ptp_nearest_idx]
            print("Candidatos reuniones formales (relajados):")
            print(rf_candidate_idx)
            if not rf_candidate_idx:
                rf_candidate_idx = [k for k, v in areas.items() if k in ptp_nearest_idx]

        # En caso que se haya encontrado mas de un candidato que cumpla con algun criterio, se elige el de mayor area
        if len(rf_candidate_idx) > 1:
            for c in rf_candidate_idx:
                rf_candidate_zones[c] = areas[c]
            rf_candidate_zones_areas = {k: v.area for k, v in rf_candidate_zones.items()}
            rf_selected_zone_idx = max(rf_candidate_zones_areas, key=rf_candidate_zones_areas.get)
            rf_selected_zone = rf_candidate_zones[rf_selected_zone_idx]
        else:
            rf_selected_zone_idx = rf_candidate_idx[0]
            rf_selected_zone = areas[rf_selected_zone_idx]

        zones.append([rf_selected_zone, 'ZONA SALAS REUNION FORMAL'])
        areas.pop(rf_selected_zone_idx, None)
        shafts_adj_qty.pop(rf_selected_zone_idx, None)
        crystal_adj_qty.pop(rf_selected_zone_idx, None)
        entrances_adj_qty.pop(rf_selected_zone_idx, None)

        # Zona reuniones informales (o puestos de trabajo informal)
        # Se buscan como candidatos, indices de areas disponibles cercanas a la zonas seleccionadas como puestos de trabajo
        ri_candidate_idx = []
        for pt in pt_selected_zones:
            pt_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(pt.bounds, objects=True))))
            for k,v in areas.items():
                if v.bounds in pt_nearest and not k in ri_candidate_idx:
                    ri_candidate_idx.append(k)
        print("Candidatos reuniones informales:", ri_candidate_idx)

        # En caso que se haya encontrado mas de un candidato que cumpla con algun criterio, se elige el de mayor area
        if len(ri_candidate_idx) > 1:
            ri_candidate_zones = {}
            for c in ri_candidate_idx:
                ri_candidate_zones[c] = areas[c]
            ri_candidate_zones_areas = {k: v.area for k, v in ri_candidate_zones.items()}
            ri_selected_zone_idx = max(ri_candidate_zones_areas, key=ri_candidate_zones_areas.get)
            ri_selected_zone = ri_candidate_zones[ri_selected_zone_idx]
        else:
            ri_selected_zone_idx = ri_candidate_idx[0]
            ri_selected_zone = areas[ri_selected_zone_idx]
        
        zones.append([ri_selected_zone, 'ZONA PUESTOS DE TRABAJO INFORMAL'])
        areas.pop(ri_selected_zone_idx, None)
        shafts_adj_qty.pop(ri_selected_zone_idx, None)
        crystal_adj_qty.pop(ri_selected_zone_idx, None)
        entrances_adj_qty.pop(ri_selected_zone_idx, None)

        if 7 in cat_area and len(areas) > 0:
            # Indices de areas cercanas a zona de soporte
            sp_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(sp_selected_zone.bounds, objects=True))))
            esp_candidate_idx = [k for k,v in areas.items() if v.bounds in sp_nearest]
            print("Candidatos reuniones informales:", esp_candidate_idx)
            if len(esp_candidate_idx) > 1:
                for c in esp_candidate_idx:
                    esp_candidate_zones[c] = areas[c]
                    esp_candidate_zones_areas = {k: v.area for k, v in esp_candidate_zones.items()}
                    esp_selected_zone_idx = min(esp_candidate_zones_areas, key=esp_candidate_zones_areas.get)
                    esp_selected_zone = esp_candidate_zones[esp_selected_zone_idx]
            else:
                esp_selected_zone_idx = esp_candidate_idx[0]
                esp_selected_zone = areas[esp_selected_zone_idx]
            zones.append([esp_selected_zone, 'ZONA ESPECIALES'])
            areas.pop(esp_selected_zone_idx, None)
            shafts_adj_qty.pop(esp_selected_zone_idx, None)
            crystal_adj_qty.pop(esp_selected_zone_idx, None)
            entrances_adj_qty.pop(esp_selected_zone_idx, None)'''

        # Las areas que sobren se asignan como puestos de trabajo
        '''if len(areas) > 0:
            pt_candidate_idx = [k for k, v in areas.items()]
            for c in pt_candidate_idx:
                selected_zone = areas[c]
                zones.append([selected_zone, 'ZONA PUESTOS DE TRABAJO'])
                areas.pop(c, None)
                shafts_adj_qty.pop(c, None)
                crystal_adj_qty.pop(c, None)
                entrances_adj_qty.pop(c, None)'''